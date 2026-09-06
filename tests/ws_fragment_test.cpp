// The host WebSocket server must deliver a MESSAGE, not a frame, and must
// not cut a transfer that pauses.
//
// Owner, 2026-09-06: "fix the issue that is causing downloads and uploads to
// fail with partial data transfers". Two things in src/WebSocketsServer.cpp
// could do that to an upload from a browser (File Transfer's WebSocket path,
// FilesPage.html uploadFileWebSocket):
//
//   1. Every frame was handed to the firmware as a whole message and
//      continuation frames (opcode 0) were dropped. A peer that fragments a
//      send -- allowed by RFC 6455 section 5.4, and what some stacks do --
//      delivered the first slice of every chunk and lost the rest, so the
//      byte count never reached the announced size.
//   2. One 5 s SO_RCVTIMEO on every recv: a browser that pauses longer than
//      that between two bytes of a frame (reading the next slice of a file
//      it does not hold locally) had its connection closed mid-upload.
//
// This drives the real server over loopback with a hand-rolled client: a
// handshake, then masked frames built byte by byte, so the test controls
// exactly how the message is cut into frames and into TCP writes.
//
//   c++ -std=c++20 -DSIMULATOR -Isrc $(python3 tools/fw_include_flags.py)
//       -o /tmp/ws_fragment tests/ws_fragment_test.cpp src/WebSocketsServer.cpp
//       && /tmp/ws_fragment

#include "WebSocketsServer.h"

#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>

#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <thread>
#include <vector>

#include "HardwareSerial.h"
#include "TestCheck.h"
using testcheck::expect;

// The logging macros the server compiles against write here; ESP.cpp owns
// the real definition and is not linked into this test.
HWCDC Serial;

namespace {

constexpr int kHttpPort = 18470;  // the pair lands on 18470/18471

struct Event {
  WStype_t type;
  std::vector<uint8_t> payload;
};

std::vector<Event> g_events;

int connectClient() {
  const int fd = ::socket(AF_INET, SOCK_STREAM, 0);
  sockaddr_in addr{};
  addr.sin_family = AF_INET;
  addr.sin_port = htons(kHttpPort + 1);
  addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
  for (int attempt = 0; attempt < 50; attempt++) {
    if (::connect(fd, reinterpret_cast<sockaddr *>(&addr), sizeof(addr)) == 0) return fd;
    std::this_thread::sleep_for(std::chrono::milliseconds(20));
  }
  ::close(fd);
  return -1;
}

bool sendBytes(int fd, const std::vector<uint8_t> &bytes) {
  size_t off = 0;
  while (off < bytes.size()) {
    const ssize_t n = ::send(fd, bytes.data() + off, bytes.size() - off, 0);
    if (n <= 0) return false;
    off += static_cast<size_t>(n);
  }
  return true;
}

bool handshake(int fd) {
  const std::string request =
      "GET / HTTP/1.1\r\nHost: 127.0.0.1\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
      "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\nSec-WebSocket-Version: 13\r\n\r\n";
  if (!sendBytes(fd, std::vector<uint8_t>(request.begin(), request.end()))) return false;
  std::string reply;
  char buf[512];
  while (reply.find("\r\n\r\n") == std::string::npos) {
    const ssize_t n = ::recv(fd, buf, sizeof(buf), 0);
    if (n <= 0) return false;
    reply.append(buf, static_cast<size_t>(n));
  }
  return reply.rfind("HTTP/1.1 101", 0) == 0;
}

// One client-to-server frame: masked, as a browser sends them.
std::vector<uint8_t> frame(uint8_t opcode, bool fin, const std::vector<uint8_t> &payload) {
  std::vector<uint8_t> out;
  out.push_back(static_cast<uint8_t>((fin ? 0x80 : 0x00) | opcode));
  if (payload.size() < 126) {
    out.push_back(static_cast<uint8_t>(0x80 | payload.size()));
  } else if (payload.size() < 65536) {
    out.push_back(0x80 | 126);
    out.push_back(static_cast<uint8_t>(payload.size() >> 8));
    out.push_back(static_cast<uint8_t>(payload.size() & 0xff));
  } else {
    out.push_back(0x80 | 127);
    for (int i = 7; i >= 0; i--) out.push_back(static_cast<uint8_t>((payload.size() >> (i * 8)) & 0xff));
  }
  const uint8_t mask[4] = {0x12, 0x34, 0x56, 0x78};
  out.insert(out.end(), mask, mask + 4);
  for (size_t i = 0; i < payload.size(); i++) out.push_back(payload[i] ^ mask[i % 4]);
  return out;
}

std::vector<uint8_t> pattern(size_t n, uint8_t seed) {
  std::vector<uint8_t> v(n);
  for (size_t i = 0; i < n; i++) v[i] = static_cast<uint8_t>(seed + i * 7 + (i >> 8));
  return v;
}

// Pump the server's event queue on this thread, as the firmware's loop() does,
// until `count` events have arrived or the wait runs out.
bool waitForEvents(WebSocketsServer &ws, size_t count, int seconds) {
  const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(seconds);
  while (std::chrono::steady_clock::now() < deadline) {
    ws.loop();
    if (g_events.size() >= count) return true;
    std::this_thread::sleep_for(std::chrono::milliseconds(10));
  }
  ws.loop();
  return g_events.size() >= count;
}

}  // namespace

int main() {
  setenv("CROSSPOINT_SIM_HTTP_PORT", std::to_string(kHttpPort).c_str(), 1);
  setenv("CROSSPOINT_SIM_BIND_ALL", "0", 1);

  WebSocketsServer ws(81);
  ws.onEvent([](uint8_t, WStype_t type, uint8_t *payload, size_t length) {
    g_events.push_back({type, std::vector<uint8_t>(payload, payload + length)});
  });
  ws.begin();

  const int fd = connectClient();
  expect(fd >= 0, "client connects to the WebSocket port");
  expect(handshake(fd), "handshake is answered with 101");
  expect(waitForEvents(ws, 1, 5) && g_events[0].type == WStype_CONNECTED, "CONNECTED event");

  // 1. A single-frame TEXT message is what the upload's START is.
  const std::string start = "START:book.epub:10000:/";
  expect(sendBytes(fd, frame(0x1, true, std::vector<uint8_t>(start.begin(), start.end()))),
         "START frame sent");
  expect(waitForEvents(ws, 2, 5) && g_events[1].type == WStype_TEXT &&
             std::string(g_events[1].payload.begin(), g_events[1].payload.end()) == start,
         "a whole TEXT frame arrives as one TEXT message");

  // 2. A BIN message fragmented across three frames, with a ping between the
  //    fragments, must arrive as ONE BIN event carrying every byte in order.
  const auto body = pattern(10000, 3);
  std::vector<uint8_t> first(body.begin(), body.begin() + 4000);
  std::vector<uint8_t> second(body.begin() + 4000, body.begin() + 8000);
  std::vector<uint8_t> third(body.begin() + 8000, body.end());
  expect(sendBytes(fd, frame(0x2, false, first)), "first fragment sent");
  expect(sendBytes(fd, frame(0x9, true, {'p', 'i', 'n', 'g'})), "ping between fragments sent");
  expect(sendBytes(fd, frame(0x0, false, second)), "middle fragment sent");
  expect(sendBytes(fd, frame(0x0, true, third)), "final fragment sent");
  expect(waitForEvents(ws, 3, 5), "the fragmented message produces an event");
  expect(g_events.size() == 3, "exactly one event for the three fragments");
  expect(g_events[2].type == WStype_BIN, "the assembled message is BIN");
  expect(g_events[2].payload == body, "the assembled message carries all 10000 bytes in order");

  // 3. A frame whose bytes arrive in two TCP writes six seconds apart -- past
  //    the 5 s that used to close the socket -- is still received whole.
  const auto slow = pattern(3000, 9);
  const auto slowFrame = frame(0x2, true, slow);
  const std::vector<uint8_t> head(slowFrame.begin(), slowFrame.begin() + 1000);
  const std::vector<uint8_t> tail(slowFrame.begin() + 1000, slowFrame.end());
  expect(sendBytes(fd, head), "first third of a frame sent");
  std::this_thread::sleep_for(std::chrono::seconds(6));
  expect(sendBytes(fd, tail), "rest of the frame sent after a 6 s pause");
  expect(waitForEvents(ws, 4, 5) && g_events[3].type == WStype_BIN && g_events[3].payload == slow,
         "a frame that paused 6 s mid-way still arrives whole");

  // 4. A clean close from the peer ends the session with DISCONNECTED.
  expect(sendBytes(fd, frame(0x8, true, {})), "close frame sent");
  expect(waitForEvents(ws, 5, 5) && g_events[4].type == WStype_DISCONNECTED, "DISCONNECTED after close");

  ::close(fd);
  ws.close();
  std::puts("PASS: fragmented and paused WebSocket messages arrive whole");
  return 0;
}
