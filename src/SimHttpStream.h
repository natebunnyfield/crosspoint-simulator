#pragma once

// STREAMING host HTTP for the esp_http_client open/read shim.
//
// Why (owner ruling 2026-09-26, S-042, "Fix both"): every host transport used
// to buffer a whole response before the firmware saw its first byte
// (sim_http_fetch::fetch fills Response.body). The firmware's read loop
// (HttpDownloader runGet: esp_http_client_open, then esp_http_client_read in
// 1 KB pieces) and the updaters' per-chunk progress were therefore fed in one
// burst at the END of each file -- so on a phone Update Fonts / Update Library
// showed "0.0 of 8.2 MB" for the whole of a file and only the elapsed clock
// moved. Here the bytes reach the reader as they arrive.
//
// Shape. A Stream is shared state between one PRODUCER (the transport: an
// NSURLSession delegate on iOS, a libcurl thread on the Mac) and one CONSUMER
// (the firmware thread calling esp_http_client_read). The consumer blocks
// until bytes, the end, or an error. The producer blocks when more than
// kStreamCapBytes are waiting, so a card slower than the link costs at most
// that much memory, never a whole file (NSURLSession has no flow control of its
// own; blocking its private delegate queue is the backpressure). abort() -- the
// firmware closing the client early, e.g. an abandoned family -- wakes both
// sides and cancels the transfer.
//
// Fixture paths (CROSSPOINT_SIM_HTTP_MOCK_ROOT, file://) and the Linux curl
// SUBPROCESS stay buffered: they are filled into a Stream in one piece, which
// behaves exactly as the old shim did.

#include <condition_variable>
#include <cstdint>
#include <cstring>
#include <functional>
#include <map>
#include <memory>
#include <mutex>
#include <string>
#include <thread>

#include "SimHttpFetch.h"

namespace sim_http_fetch {

inline constexpr size_t kStreamCapBytes = 1024 * 1024;

class Stream {
 public:
  // ---- producer side ------------------------------------------------------
  // The final response's status and declared length (-1 = none declared).
  // Idempotent: the first call wins (a redirect's hop never reaches here --
  // both host transports follow redirects themselves).
  void setHeaders(int status, int64_t contentLength) {
    std::lock_guard<std::mutex> lock(m_);
    if (headersReady_) return;
    status_ = status;
    contentLength_ = contentLength;
    headersReady_ = true;
    cv_.notify_all();
  }
  // Appends bytes; blocks while kStreamCapBytes are unread. False once aborted:
  // the producer must stop.
  bool push(const char *data, size_t len) {
    std::unique_lock<std::mutex> lock(m_);
    cv_.wait(lock, [&] { return aborted_ || buf_.size() - off_ < kStreamCapBytes; });
    if (aborted_) return false;
    if (off_ > 0 && off_ == buf_.size()) {
      buf_.clear();
      off_ = 0;
    } else if (off_ > kStreamCapBytes) {
      buf_.erase(0, off_);
      off_ = 0;
    }
    buf_.append(data, len);
    received_ += len;
    cv_.notify_all();
    return true;
  }
  // The transfer ended. transportError is a curl exit code (0 = clean).
  void finish(int transportError) {
    std::lock_guard<std::mutex> lock(m_);
    if (done_) return;
    transportError_ = transportError;
    headersReady_ = true;  // a transfer that died before any header is still "answered"
    done_ = true;
    cv_.notify_all();
  }
  bool aborted() const {
    std::lock_guard<std::mutex> lock(m_);
    return aborted_;
  }

  // ---- consumer side ------------------------------------------------------
  void waitHeaders() {
    std::unique_lock<std::mutex> lock(m_);
    cv_.wait(lock, [&] { return headersReady_ || aborted_; });
  }
  int status() const {
    std::lock_guard<std::mutex> lock(m_);
    return status_;
  }
  int64_t contentLength() const {
    std::lock_guard<std::mutex> lock(m_);
    return contentLength_;
  }
  // "The server answered": a status line, a byte, or a clean end. The old
  // shim's acceptance rule (fetch() == true), so open() fails exactly when it
  // used to.
  bool answered() const {
    std::lock_guard<std::mutex> lock(m_);
    return status_ > 0 || received_ > 0 || (done_ && transportError_ == 0);
  }
  // Up to `len` bytes: blocks until some arrive. 0 = the body ended cleanly,
  // -1 = the transfer failed (or was aborted) with nothing left to hand over.
  int read(char *out, int len) {
    if (len <= 0) return -1;
    std::unique_lock<std::mutex> lock(m_);
    cv_.wait(lock, [&] { return aborted_ || off_ < buf_.size() || done_; });
    if (off_ < buf_.size()) {
      const size_t n = std::min(static_cast<size_t>(len), buf_.size() - off_);
      std::memcpy(out, buf_.data() + off_, n);
      off_ += n;
      cv_.notify_all();  // room for the producer
      return static_cast<int>(n);
    }
    if (aborted_) return -1;
    return transportError_ == 0 ? 0 : -1;
  }
  // Every byte arrived, none is left unread, the transport ended cleanly, and
  // the declared length (if any) was met.
  bool complete() const {
    std::lock_guard<std::mutex> lock(m_);
    return done_ && !aborted_ && transportError_ == 0 && off_ == buf_.size() &&
           (contentLength_ < 0 || static_cast<int64_t>(received_) == contentLength_);
  }
  size_t received() const {
    std::lock_guard<std::mutex> lock(m_);
    return received_;
  }
  int transportError() const {
    std::lock_guard<std::mutex> lock(m_);
    return transportError_;
  }

  // Either side, idempotent. Wakes both and runs the transport's cancel.
  void abort() {
    std::function<void()> cancel;
    {
      std::lock_guard<std::mutex> lock(m_);
      if (aborted_) return;
      aborted_ = true;
      if (!done_) cancel = std::move(cancel_);
      cv_.notify_all();
    }
    if (cancel) cancel();
  }
  void setCancel(std::function<void()> fn) {
    std::lock_guard<std::mutex> lock(m_);
    cancel_ = std::move(fn);
  }

  // A whole response at once (fixtures, the curl subprocess).
  void fillBuffered(const Response &r, bool ok) {
    setHeaders(r.statusCode, r.statusCode > 0 ? static_cast<int64_t>(r.body.size()) : -1);
    // Appended directly, NOT through push(): nobody is reading yet (this runs
    // before openStream returns), so a fixture over the cap would block forever.
    {
      std::lock_guard<std::mutex> lock(m_);
      buf_.append(r.body);
      received_ += r.body.size();
    }
    finish(ok ? 0 : (r.curlExitCode ? r.curlExitCode : 7));
  }

 private:
  mutable std::mutex m_;
  std::condition_variable cv_;
  bool headersReady_ = false;
  bool done_ = false;
  bool aborted_ = false;
  int status_ = 0;
  int transportError_ = 0;
  int64_t contentLength_ = -1;
  std::string buf_;
  size_t off_ = 0;
  size_t received_ = 0;
  std::function<void()> cancel_;
};

#if CROSSPOINT_SIM_HOST_HTTP
// Implemented by the platform (ios/CrossPointHttp.mm): starts the request and
// feeds `stream` from the transport's own queue. Returns false when it could
// not even start (the caller then finishes the stream with an error).
bool hostOpenStream(const std::string &url, const char *method,
                    const std::map<std::string, std::string> &headers,
                    const std::string &basicAuth, const char *body,
                    const std::shared_ptr<Stream> &stream);
#endif

#if CROSSPOINT_SIM_LIBCURL
namespace detail {
struct CurlStreamCtx {
  std::shared_ptr<Stream> stream;
  CURL *handle = nullptr;
  bool announced = false;
};
inline void curlAnnounce(CurlStreamCtx &c) {
  if (c.announced) return;
  c.announced = true;
  long status = 0;
  curl_easy_getinfo(c.handle, CURLINFO_RESPONSE_CODE, &status);
  curl_off_t len = -1;
  curl_easy_getinfo(c.handle, CURLINFO_CONTENT_LENGTH_DOWNLOAD_T, &len);
  c.stream->setHeaders(static_cast<int>(status), len >= 0 ? static_cast<int64_t>(len) : -1);
}
inline size_t curlStreamWrite(char *ptr, size_t size, size_t nmemb, void *userdata) {
  auto &c = *static_cast<CurlStreamCtx *>(userdata);
  curlAnnounce(c);
  const size_t bytes = size * nmemb;
  return c.stream->push(ptr, bytes) ? bytes : 0;  // 0 aborts the transfer
}
// Checked about once a second even while no byte moves, so an abort lands on a
// stalled link too.
inline int curlStreamProgress(void *userdata, curl_off_t, curl_off_t, curl_off_t, curl_off_t) {
  return static_cast<CurlStreamCtx *>(userdata)->stream->aborted() ? 1 : 0;
}
}  // namespace detail

// libcurl on its own thread, feeding the stream. The thread is DETACHED and
// owns a reference to the stream, so a consumer that gives up never waits for
// a stalled peer to time out; the progress callback ends the transfer shortly
// after abort().
inline void openLibcurlStream(const std::string &url, const char *method,
                              const std::map<std::string, std::string> &headers,
                              const std::string &basicAuth, const char *body,
                              const std::shared_ptr<Stream> &stream) {
  libcurlInitOnce();
  std::string m = method ? method : "GET";
  std::string b = body ? body : "";
  const bool hasBody = body != nullptr;
  std::thread([url, m, headers, basicAuth, b, hasBody, stream]() {
    CURL *handle = curl_easy_init();
    if (!handle) {
      stream->finish(2);  // CURLE_FAILED_INIT
      return;
    }
    detail::CurlStreamCtx ctx{stream, handle, false};
    struct curl_slist *headerList = nullptr;
    for (const auto &header : headers)
      headerList = curl_slist_append(headerList, (header.first + ": " + header.second).c_str());
    // The same options as fetchWithLibcurl, in the same order.
    curl_easy_setopt(handle, CURLOPT_URL, url.c_str());
    curl_easy_setopt(handle, CURLOPT_FOLLOWLOCATION, 1L);
    curl_easy_setopt(handle, CURLOPT_CONNECTTIMEOUT, 10L);
    curl_easy_setopt(handle, CURLOPT_LOW_SPEED_LIMIT, 1L);
    curl_easy_setopt(handle, CURLOPT_LOW_SPEED_TIME, 60L);
    curl_easy_setopt(handle, CURLOPT_NOSIGNAL, 1L);
    curl_easy_setopt(handle, CURLOPT_WRITEFUNCTION, detail::curlStreamWrite);
    curl_easy_setopt(handle, CURLOPT_WRITEDATA, &ctx);
    curl_easy_setopt(handle, CURLOPT_NOPROGRESS, 0L);
    curl_easy_setopt(handle, CURLOPT_XFERINFOFUNCTION, detail::curlStreamProgress);
    curl_easy_setopt(handle, CURLOPT_XFERINFODATA, &ctx);
    if (m != "GET") curl_easy_setopt(handle, CURLOPT_CUSTOMREQUEST, m.c_str());
    if (headerList) curl_easy_setopt(handle, CURLOPT_HTTPHEADER, headerList);
    if (!basicAuth.empty()) {
      curl_easy_setopt(handle, CURLOPT_HTTPAUTH, (long)CURLAUTH_BASIC);
      curl_easy_setopt(handle, CURLOPT_USERPWD, basicAuth.c_str());
    }
    if (hasBody) curl_easy_setopt(handle, CURLOPT_COPYPOSTFIELDS, b.c_str());
    const CURLcode rc = curl_easy_perform(handle);
    detail::curlAnnounce(ctx);  // a bodiless answer (204, an empty 404) still has headers
    curl_slist_free_all(headerList);
    curl_easy_cleanup(handle);
    stream->finish(static_cast<int>(rc));
  }).detach();
}
#endif  // CROSSPOINT_SIM_LIBCURL

// Starts a request and returns its stream at once; the caller waits for the
// headers (Stream::waitHeaders). Same dispatch order as fetch(): fixtures
// first, then the platform's transport.
inline std::shared_ptr<Stream> openStream(const std::string &url, const char *method,
                                          const std::map<std::string, std::string> &headers,
                                          const std::string &basicAuth, const char *body) {
  auto stream = std::make_shared<Stream>();
  if (sim_update_trace::active()) {
    const std::string bare = url.substr(0, url.find('?'));
    sim_update_trace::mark("host stream open", bare.c_str());
  }
  Response fixture;
  if (fetchFromMockRoot(url, fixture) || fetchFromFileUrl(url, fixture)) {
    stream->fillBuffered(fixture, true);
    return stream;
  }
#if CROSSPOINT_SIM_HOST_HTTP
  if (!hostOpenStream(url, method, headers, basicAuth, body, stream)) stream->finish(7);
#elif CROSSPOINT_SIM_LIBCURL
  openLibcurlStream(url, method, headers, basicAuth, body, stream);
#else
  // The Linux curl SUBPROCESS: buffered, as before.
  Response r;
  const bool ok = fetchWithCurl(url, method, headers, basicAuth, body, r);
  stream->fillBuffered(r, ok);
#endif
  return stream;
}

}  // namespace sim_http_fetch
