// src/SimHttpStream.h -- streaming host HTTP behind esp_http_client_open/read.
//
// S-042, owner ruling 2026-09-26: the updaters' byte counters must move WITHIN
// a file on the phone. They only can if the transport hands bytes over as they
// arrive; every host transport used to buffer the whole body first. Pinned:
//   * Stream: bytes are readable before the transfer ends; a clean end reads 0,
//     a failed one -1; complete() needs the declared length; the producer is
//     HELD at kStreamCapBytes (no whole-file buffering); abort() wakes a
//     blocked producer AND a blocked reader and runs the transport's cancel.
//   * A fixture larger than the cap does not deadlock the open (it is filled
//     before anyone reads).
//   * The esp_http_client shim over a real socket (libcurl, the Mac's
//     transport): the FIRST chunk is read while the server is still holding
//     the rest back -- which the old buffered shim could never do, it would
//     block in open() until the server finished. Fails against it.
//
//   c++ -std=c++20 -Isrc tests/http_stream_test.cpp [-lcurl]

#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>

#include <atomic>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <string>
#include <thread>

#include "esp_http_client.h"

using namespace std::chrono_literals;
using sim_http_fetch::Stream;

namespace {
int g_failures = 0;
void check(bool ok, const char *what) {
  if (!ok) {
    std::printf("FAIL: %s\n", what);
    g_failures++;
  }
}
}  // namespace

#if CROSSPOINT_SIM_HOST_HTTP
namespace sim_http_fetch {
bool hostFetch(const std::string &, const char *, const std::map<std::string, std::string> &,
               const std::string &, const char *, Response &) {
  return false;
}
bool hostOpenStream(const std::string &, const char *, const std::map<std::string, std::string> &,
                    const std::string &, const char *, const std::shared_ptr<Stream> &) {
  return false;
}
}  // namespace sim_http_fetch
#endif

int main() {
  // --- Stream: incremental delivery and the end states ---------------------
  {
    auto s = std::make_shared<Stream>();
    s->setHeaders(200, 10);
    check(s->push("hello", 5), "push accepted");
    char buf[16];
    check(s->read(buf, sizeof buf) == 5, "bytes are readable before the transfer ends");
    check(!s->complete(), "not complete mid-transfer");
    s->push("world", 5);
    s->finish(0);
    check(s->read(buf, sizeof buf) == 5, "the rest");
    check(s->read(buf, sizeof buf) == 0, "a clean end reads 0");
    check(s->complete(), "complete once every declared byte is read");
  }
  {
    auto s = std::make_shared<Stream>();
    s->setHeaders(200, 10);
    s->push("hello", 5);
    s->finish(0);
    char buf[16];
    s->read(buf, sizeof buf);
    check(!s->complete(), "short of the declared length is not complete");
  }
  {
    auto s = std::make_shared<Stream>();
    s->setHeaders(200, -1);
    s->push("abc", 3);
    s->finish(56);  // connection lost
    char buf[16];
    check(s->read(buf, sizeof buf) == 3, "bytes before a failure are still handed over");
    check(s->read(buf, sizeof buf) == -1, "then the failure reads -1");
    check(!s->complete(), "a failed transfer is not complete");
  }

  // --- backpressure and abort ----------------------------------------------
  {
    auto s = std::make_shared<Stream>();
    s->setHeaders(200, -1);
    std::atomic<size_t> pushed{0};
    std::atomic<bool> producerDone{false};
    std::atomic<bool> cancelled{false};
    s->setCancel([&] { cancelled = true; });
    std::thread producer([&] {
      std::string chunk(64 * 1024, 'x');
      while (s->push(chunk.data(), chunk.size())) pushed += chunk.size();
      producerDone = true;
    });
    std::this_thread::sleep_for(200ms);
    check(pushed.load() <= sim_http_fetch::kStreamCapBytes,
          "the producer is held at the cap while nobody reads");
    check(!producerDone.load(), "the held producer is still waiting");
    s->abort();
    producer.join();
    check(producerDone.load(), "abort wakes a blocked producer");
    check(cancelled.load(), "abort runs the transport's cancel");
  }
  {
    auto s = std::make_shared<Stream>();
    s->setHeaders(200, -1);
    std::atomic<int> got{1};
    std::thread reader([&] {
      char b[8];
      got = s->read(b, sizeof b);
    });
    std::this_thread::sleep_for(100ms);
    s->abort();
    reader.join();
    check(got.load() == -1, "abort wakes a blocked reader with -1");
  }

  // --- a fixture larger than the cap does not deadlock the open ------------
  {
    char dir[] = "/tmp/http-stream-test-XXXXXX";
    if (!mkdtemp(dir)) return 1;
    const std::string big(3 * sim_http_fetch::kStreamCapBytes, 'b');
    std::ofstream(std::string(dir) + "/big.bin", std::ios::binary) << big;
    setenv("CROSSPOINT_SIM_HTTP_MOCK_ROOT", dir, 1);
    esp_http_client_config_t cfg{};
    cfg.url = "https://example.invalid/big.bin";
    auto *c = esp_http_client_init(&cfg);
    check(esp_http_client_open(c, 0) == ESP_OK, "fixture open");
    check(esp_http_client_fetch_headers(c) == static_cast<int64_t>(big.size()), "fixture length");
    size_t total = 0;
    char buf[1024];
    int n;
    while ((n = esp_http_client_read(c, buf, sizeof buf)) > 0) total += n;
    check(n == 0 && total == big.size(), "the whole fixture reads back");
    check(esp_http_client_is_complete_data_received(c), "fixture complete");
    esp_http_client_cleanup(c);
    unsetenv("CROSSPOINT_SIM_HTTP_MOCK_ROOT");
    std::remove((std::string(dir) + "/big.bin").c_str());
    rmdir(dir);
  }

#if CROSSPOINT_SIM_LIBCURL
  // --- the real Mac transport over a socket: first chunk before the end ----
  {
    const int srv = socket(AF_INET, SOCK_STREAM, 0);
    int one = 1;
    setsockopt(srv, SOL_SOCKET, SO_REUSEADDR, &one, sizeof one);
    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    addr.sin_port = 0;
    bind(srv, reinterpret_cast<sockaddr *>(&addr), sizeof addr);
    listen(srv, 1);
    socklen_t len = sizeof addr;
    getsockname(srv, reinterpret_cast<sockaddr *>(&addr), &len);
    const int port = ntohs(addr.sin_port);

    std::atomic<bool> firstRead{false};
    std::atomic<bool> releasedEarly{false};
    std::thread server([&] {
      const int c = accept(srv, nullptr, nullptr);
      char req[4096];
      (void)recv(c, req, sizeof req, 0);
      const std::string head = "HTTP/1.1 200 OK\r\nContent-Length: 8192\r\nConnection: close\r\n\r\n";
      const std::string half(4096, 'a');
      send(c, head.data(), head.size(), 0);
      send(c, half.data(), half.size(), 0);
      // Hold the second half until the client has READ some of the first --
      // or 3 s, after which the test has failed anyway.
      for (int i = 0; i < 300 && !firstRead.load(); i++) std::this_thread::sleep_for(10ms);
      releasedEarly = firstRead.load();
      send(c, half.data(), half.size(), 0);
      close(c);
    });
    const std::string url = "http://127.0.0.1:" + std::to_string(port) + "/f";
    esp_http_client_config_t cfg{};
    cfg.url = url.c_str();
    auto *c = esp_http_client_init(&cfg);
    check(esp_http_client_open(c, 0) == ESP_OK, "socket open");
    check(esp_http_client_fetch_headers(c) == 8192, "declared length from the headers");
    char buf[1024];
    const int first = esp_http_client_read(c, buf, sizeof buf);
    check(first > 0, "a first chunk arrives");
    firstRead = true;
    size_t total = first > 0 ? first : 0;
    int n;
    while ((n = esp_http_client_read(c, buf, sizeof buf)) > 0) total += n;
    check(n == 0 && total == 8192, "the whole body");
    check(esp_http_client_is_complete_data_received(c), "socket body complete");
    esp_http_client_cleanup(c);
    server.join();
    close(srv);
    check(releasedEarly.load(), "the first chunk was READ while the server still held the rest back");
  }
#endif

  if (g_failures == 0) std::printf("http_stream: all checks passed\n");
  return g_failures == 0 ? 0 : 1;
}
