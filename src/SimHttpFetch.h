#pragma once

#include <array>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <map>
#include <string>

#include <dirent.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <unistd.h>

#include "SimUpdateTrace.h"

#if defined(__APPLE__)
#include <TargetConditionals.h>
#endif

// Whether a host HTTP client stands in for the curl subprocess.
//
// The curl path shells out via popen(), which is fine on a developer's machine
// and impossible in a sandbox: iOS has no curl binary and forbids exec
// outright. Overridable so the host branch can be exercised off-device -- the
// real backend is iOS-only, so without this it would ship with no test at all.
#ifndef CROSSPOINT_SIM_HOST_HTTP
#if defined(__APPLE__) && TARGET_OS_IPHONE
#define CROSSPOINT_SIM_HOST_HTTP 1
#else
#define CROSSPOINT_SIM_HOST_HTTP 0
#endif
#endif

// Whether libcurl THE LIBRARY stands in for the curl SUBPROCESS.
//
// The same problem as the iOS branch above, one platform over: popen() spawns a
// binary outside the bundle, which the macOS App Sandbox forbids. Every
// OPDS/catalog download, KOReader sync and SD-font fetch therefore fails in a
// sandboxed Mac build no matter which network entitlement is granted --
// packaging/macos/CrossPoint.entitlements says exactly that in its own header.
// A library call has no subprocess to forbid. It is the same curl either way,
// and notably the same CURLcode numbers, which ARE the CLI's exit codes, so
// simCurlExitCodeToHttpError() keeps working untouched.
//
// DECIDED HERE, IN THE HEADER, NOT BY A BUILD FLAG. Every TU that includes this
// must agree -- simulator and firmware alike, since firmware code includes the
// HTTPClient.h shim -- or these inline functions differ between TUs, which is an
// ODR violation rather than an error anything reports. A flag is easy to set on
// one env and miss on another; a platform test cannot be. All the build has to
// do is LINK -lcurl, and forgetting that is a loud undefined-symbol error
// naming curl_easy_init, which diagnoses itself.
//
// Linux keeps the subprocess: no sandbox forbids it there, and switching would
// put a libcurl-dev requirement on every Linux/WSL checkout for no gain.
// Overridable, which is how the test below compiles this branch off-Mac.
#ifndef CROSSPOINT_SIM_LIBCURL
#if defined(__APPLE__) && !TARGET_OS_IPHONE
#define CROSSPOINT_SIM_LIBCURL 1
#else
#define CROSSPOINT_SIM_LIBCURL 0
#endif
#endif

#if CROSSPOINT_SIM_LIBCURL
#include <curl/curl.h>
#include <mutex>
#endif

namespace sim_http_fetch {

struct Response {
  int statusCode = 0;
  // Kept named for curl even when a host client produced it: HTTPClient.h maps
  // these through simCurlExitCodeToHttpError() into the HTTPC_ERROR_* codes the
  // firmware branches on, so a host backend reports failures in curl's
  // vocabulary rather than introducing a second error space.
  int curlExitCode = 0;
  std::string body;
};

#if CROSSPOINT_SIM_HOST_HTTP
// Implemented by the platform (ios/CrossPointHttp.mm). Synchronous, and must
// never be called from the SDL main thread -- firmware download paths run on
// task threads and that has to stay true.
bool hostFetch(const std::string &url, const char *method,
               const std::map<std::string, std::string> &headers,
               const std::string &basicAuth, const char *body, Response &out);
#endif

inline bool startsWith(const std::string &value, const char *prefix) {
  return value.rfind(prefix, 0) == 0;
}

inline std::string shellQuote(const std::string &value) {
  std::string out = "'";
  for (char c : value) {
    if (c == '\'')
      out += "'\\''";
    else
      out += c;
  }
  out += "'";
  return out;
}

inline int hexValue(char c) {
  if (c >= '0' && c <= '9')
    return c - '0';
  if (c >= 'a' && c <= 'f')
    return c - 'a' + 10;
  if (c >= 'A' && c <= 'F')
    return c - 'A' + 10;
  return -1;
}

inline std::string urlDecode(std::string value) {
  std::string out;
  out.reserve(value.size());
  for (size_t i = 0; i < value.size(); ++i) {
    if (value[i] == '%' && i + 2 < value.size()) {
      int hi = hexValue(value[i + 1]);
      int lo = hexValue(value[i + 2]);
      if (hi >= 0 && lo >= 0) {
        out.push_back(static_cast<char>((hi << 4) | lo));
        i += 2;
        continue;
      }
    }
    out.push_back(value[i]);
  }
  return out;
}

inline std::string basenameFromUrl(const std::string &url) {
  size_t end = url.find_first_of("?#");
  std::string path = url.substr(0, end == std::string::npos ? url.size() : end);
  size_t slash = path.find_last_of('/');
  return urlDecode(slash == std::string::npos ? path : path.substr(slash + 1));
}

inline bool readFile(const std::string &path, std::string &out) {
  FILE *file = std::fopen(path.c_str(), "rb");
  if (!file)
    return false;

  out.clear();
  std::array<char, 8192> buffer{};
  while (true) {
    size_t n = std::fread(buffer.data(), 1, buffer.size(), file);
    if (n > 0)
      out.append(buffer.data(), n);
    if (n < buffer.size()) {
      if (std::ferror(file)) {
        std::fclose(file);
        return false;
      }
      break;
    }
  }

  std::fclose(file);
  return true;
}

inline bool isDirectory(const std::string &path) {
  struct stat st{};
  return stat(path.c_str(), &st) == 0 && S_ISDIR(st.st_mode);
}

inline bool findFileByBasename(const std::string &dir, const std::string &name,
                               std::string &outPath, int depth = 0) {
  if (depth > 5)
    return false;

  DIR *handle = opendir(dir.c_str());
  if (!handle)
    return false;

  while (dirent *entry = readdir(handle)) {
    std::string entryName = entry->d_name;
    if (entryName == "." || entryName == "..")
      continue;

    std::string path = dir;
    if (!path.empty() && path.back() != '/')
      path += '/';
    path += entryName;

    if (entryName == name) {
      outPath = path;
      closedir(handle);
      return true;
    }

    if (isDirectory(path) &&
        findFileByBasename(path, name, outPath, depth + 1)) {
      closedir(handle);
      return true;
    }
  }

  closedir(handle);
  return false;
}

inline bool fetchFromFileUrl(const std::string &url, Response &out) {
  if (!startsWith(url, "file://"))
    return false;

  std::string path = urlDecode(url.substr(strlen("file://")));
  if (startsWith(path, "localhost/"))
    path = path.substr(strlen("localhost"));

  if (readFile(path, out.body)) {
    out.statusCode = 200;
  } else {
    out.body.clear();
    out.statusCode = 404;
  }
  return true;
}

inline bool fetchFromMockRoot(const std::string &url, Response &out) {
  const char *root = std::getenv("CROSSPOINT_SIM_HTTP_MOCK_ROOT");
  if (!root || root[0] == '\0')
    return false;

  std::string name = basenameFromUrl(url);
  if (name.empty() || name == "." || name == ".." ||
      name.find('/') != std::string::npos ||
      name.find('\\') != std::string::npos) {
    return false;
  }

  std::string path = root;
  if (!path.empty() && path.back() != '/')
    path += '/';
  path += name;

  if (!readFile(path, out.body)) {
    std::string nestedPath;
    if (!findFileByBasename(root, name, nestedPath) ||
        !readFile(nestedPath, out.body))
      return false;
  }

  if (!out.body.empty()) {
    out.statusCode = 200;
    return true;
  }
  return false;
}

// The curl invocation, built where a test can read it.
//
// TIMEOUTS ARE IDLE, NOT TOTAL. This carried `--max-time 60` until
// 2026-09-06, a cap on the WHOLE transfer: a download that was moving
// perfectly well was killed at sixty seconds, and Update Library reported the
// book it was in the middle of as failed. Any book over about 60 s on the
// link -- a large epub, a slow morning -- could never be synced on the
// desktop, and the failure looked like the network. The other two transports
// were already idle-based (the device's esp_http_client uses a per-socket-op
// timeout, the phone's NSURLSession a `timeoutInterval` that resets on data),
// so the desktop was the only one that could truncate a healthy transfer:
// S-038 fixed the same class of bug on the serving side and did not reach
// this, the fetching side.
//
// `--speed-limit 1 --speed-time 60` is curl's idle timeout: abort only if the
// transfer moves less than one byte per second averaged over a 60 s window.
// A stalled peer still dies in about a minute, matching the other two; a slow
// but moving transfer runs to completion however long it takes.
// `--connect-timeout` still bounds the phase before any bytes flow.
inline std::string
curlCommand(const std::string &outPath, const std::string &url,
            const char *method,
            const std::map<std::string, std::string> &headers,
            const std::string &basicAuth, const char *body) {
  std::string cmd =
      "curl -L -sS --connect-timeout 10 --speed-limit 1 --speed-time 60 -o ";
  cmd += shellQuote(outPath);
  cmd += " -w '%{http_code}'";
  if (method && std::string(method) != "GET")
    cmd += " -X " + shellQuote(method);
  for (const auto &header : headers) {
    cmd += " -H " + shellQuote(header.first + ": " + header.second);
  }
  if (!basicAuth.empty())
    cmd += " -u " + shellQuote(basicAuth);
  if (body)
    cmd += " --data-binary " + shellQuote(body);
  cmd += " " + shellQuote(url);
  return cmd;
}

inline bool fetchWithCurl(const std::string &url, const char *method,
                          const std::map<std::string, std::string> &headers,
                          const std::string &basicAuth, const char *body,
                          Response &out) {
  char tmpTemplate[] = "/tmp/crosspoint-sim-http-XXXXXX";
  int fd = mkstemp(tmpTemplate);
  if (fd < 0)
    return false;
  close(fd);

  const std::string cmd =
      curlCommand(tmpTemplate, url, method, headers, basicAuth, body);

  FILE *pipe = popen(cmd.c_str(), "r");
  if (!pipe) {
    unlink(tmpTemplate);
    return false;
  }

  std::string statusText;
  std::array<char, 64> statusBuffer{};
  while (
      fgets(statusBuffer.data(), static_cast<int>(statusBuffer.size()), pipe)) {
    statusText += statusBuffer.data();
  }
  const int rc = pclose(pipe);
  if (rc >= 0 && WIFEXITED(rc))
    out.curlExitCode = WEXITSTATUS(rc);

  bool readOk = readFile(tmpTemplate, out.body);
  unlink(tmpTemplate);
  if (!readOk)
    out.body.clear();

  out.statusCode = std::atoi(statusText.c_str());
  return rc == 0 || out.statusCode > 0 || !out.body.empty();
}

#if CROSSPOINT_SIM_LIBCURL
inline size_t libcurlAppendBody(char *ptr, size_t size, size_t nmemb,
                                void *userdata) {
  const size_t bytes = size * nmemb;
  static_cast<std::string *>(userdata)->append(ptr, bytes);
  return bytes;
}

// curl_global_init is NOT thread-safe and libcurl's implicit init inherits
// that. fetch() runs on firmware task threads, several of which can start a
// transfer at once, so force it exactly once before any easy handle exists.
// A function-local static is the guarantee: C++11 onwards the initialiser runs
// once and other threads block until it has.
inline void libcurlInitOnce() {
  static const bool ready = [] {
    return curl_global_init(CURL_GLOBAL_DEFAULT) == CURLE_OK;
  }();
  (void)ready;
}

// The same request the curl CLI above builds, option for option. Kept in that
// order so the two can be read side by side.
inline bool fetchWithLibcurl(const std::string &url, const char *method,
                             const std::map<std::string, std::string> &headers,
                             const std::string &basicAuth, const char *body,
                             Response &out) {
  libcurlInitOnce();
  CURL *handle = curl_easy_init();
  if (!handle)
    return false;

  struct curl_slist *headerList = nullptr;
  for (const auto &header : headers) {
    headerList =
        curl_slist_append(headerList, (header.first + ": " + header.second).c_str());
  }

  curl_easy_setopt(handle, CURLOPT_URL, url.c_str());
  curl_easy_setopt(handle, CURLOPT_FOLLOWLOCATION, 1L);   // -L
  curl_easy_setopt(handle, CURLOPT_CONNECTTIMEOUT, 10L);  // --connect-timeout 10
  // The idle timeout, not a total one -- see curlCommand's note above for why
  // that distinction cost a release. --speed-limit 1 --speed-time 60.
  curl_easy_setopt(handle, CURLOPT_LOW_SPEED_LIMIT, 1L);
  curl_easy_setopt(handle, CURLOPT_LOW_SPEED_TIME, 60L);
  // Without this libcurl uses SIGALRM for DNS timeouts, which is unsafe off the
  // main thread and every caller here is off it.
  curl_easy_setopt(handle, CURLOPT_NOSIGNAL, 1L);
  curl_easy_setopt(handle, CURLOPT_WRITEFUNCTION, libcurlAppendBody);
  curl_easy_setopt(handle, CURLOPT_WRITEDATA, &out.body);
  if (method && std::strcmp(method, "GET") != 0)
    curl_easy_setopt(handle, CURLOPT_CUSTOMREQUEST, method);
  if (headerList)
    curl_easy_setopt(handle, CURLOPT_HTTPHEADER, headerList);
  if (!basicAuth.empty()) {
    curl_easy_setopt(handle, CURLOPT_HTTPAUTH, (long)CURLAUTH_BASIC);
    curl_easy_setopt(handle, CURLOPT_USERPWD, basicAuth.c_str());
  }
  if (body) {
    // COPYPOSTFIELDS, not POSTFIELDS: the latter does not copy, and would then
    // be a dangling read if a caller's buffer outlived nothing. Length is left
    // implicit (strlen) exactly as --data-binary with a C string was.
    curl_easy_setopt(handle, CURLOPT_COPYPOSTFIELDS, body);
  }

  const CURLcode rc = curl_easy_perform(handle);
  long status = 0;
  curl_easy_getinfo(handle, CURLINFO_RESPONSE_CODE, &status);

  curl_slist_free_all(headerList);
  curl_easy_cleanup(handle);

  out.curlExitCode = static_cast<int>(rc);
  out.statusCode = static_cast<int>(status);
  // Same acceptance rule as the subprocess path: a transport failure that still
  // produced a status line or a body is worth handing back.
  return rc == CURLE_OK || out.statusCode > 0 || !out.body.empty();
}
#endif // CROSSPOINT_SIM_LIBCURL

inline bool fetchUntraced(const std::string &url, const char *method,
                          const std::map<std::string, std::string> &headers,
                          const std::string &basicAuth, const char *body,
                          Response &out);

inline bool fetch(const std::string &url, const char *method,
                  const std::map<std::string, std::string> &headers,
                  const std::string &basicAuth, const char *body,
                  Response &out) {
  out = Response{};
  // The update screens' flight recorder: every host fetch while one is up,
  // with its duration and size (src/SimUpdateTrace.h). The query string is
  // dropped -- a redirect target can carry a signed one, and a URL is enough.
  if (sim_update_trace::active()) {
    const std::string bare = url.substr(0, url.find('?'));
    sim_update_trace::mark("host fetch", bare.c_str());
    const uint64_t t0 = sim_update_trace::now();
    const bool ok = fetchUntraced(url, method, headers, basicAuth, body, out);
    sim_update_trace::logf("host fetch done in %llu ms: ok=%d status=%d curl=%d bytes=%zu",
                           static_cast<unsigned long long>(sim_update_trace::now() - t0), ok ? 1 : 0,
                           out.statusCode, out.curlExitCode, out.body.size());
    sim_update_trace::mark("host fetch returned");
    return ok;
  }
  return fetchUntraced(url, method, headers, basicAuth, body, out);
}

inline bool fetchUntraced(const std::string &url, const char *method,
                          const std::map<std::string, std::string> &headers,
                          const std::string &basicAuth, const char *body,
                          Response &out) {
  out = Response{};
  // The mock-root and file:// paths are platform-independent and stay ahead of
  // any real transport: they are how scripted QA feeds fixtures in without a
  // network, and that is as useful on a phone as on a desktop.
  if (fetchFromMockRoot(url, out))
    return true;
  if (fetchFromFileUrl(url, out))
    return true;
#if CROSSPOINT_SIM_HOST_HTTP
  return hostFetch(url, method, headers, basicAuth, body, out);
#elif CROSSPOINT_SIM_LIBCURL
  return fetchWithLibcurl(url, method, headers, basicAuth, body, out);
#else
  return fetchWithCurl(url, method, headers, basicAuth, body, out);
#endif
}

} // namespace sim_http_fetch
