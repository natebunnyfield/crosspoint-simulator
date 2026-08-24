// Covers sim_http_fetch's dispatch order and the host-backend branch.
//
// Same reasoning as wifi_host_test.cpp: the real backend
// (ios/CrossPointHttp.mm) is iOS-only and cannot be compiled here, so without
// forcing CROSSPOINT_SIM_HOST_HTTP on and substituting a backend, the branch
// the phone takes would ship untested. What this pins is the part that is easy
// to get wrong and platform-independent: that the fixture paths still win over
// the network, that they win in the right order, and that the host backend
// takes over from curl rather than sitting alongside it.
//
// What it does NOT cover: NSURLSession behavior, TLS, or redirects. Those are
// device-verify items in ios/WIFI.md.
//
//   c++ -std=c++20 -Isrc -DCROSSPOINT_SIM_HOST_HTTP=1
//       tests/http_dispatch_test.cpp -o /tmp/http_dispatch_test && /tmp/http_dispatch_test

#include "SimHttpFetch.h"

#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <string>
#include "TestCheck.h"
using testcheck::expect;

#if !CROSSPOINT_SIM_HOST_HTTP
#error "build with -DCROSSPOINT_SIM_HOST_HTTP=1; see the header comment"
#endif

namespace sim_http_fetch {
namespace {
int g_hostCalls = 0;
std::string g_lastUrl;
std::string g_lastMethod;
std::string g_lastAuth;
}  // namespace

// Stand-in for the NSURLSession backend.
bool hostFetch(const std::string &url, const char *method,
               const std::map<std::string, std::string> &headers,
               const std::string &basicAuth, const char *body, Response &out) {
  (void)headers;
  (void)body;
  ++g_hostCalls;
  g_lastUrl = url;
  g_lastMethod = method ? method : "";
  g_lastAuth = basicAuth;
  out = Response{};
  out.statusCode = 200;
  out.body = "from-host-backend";
  return true;
}

int testHostCalls() { return g_hostCalls; }
const std::string &testLastUrl() { return g_lastUrl; }
const std::string &testLastMethod() { return g_lastMethod; }
const std::string &testLastAuth() { return g_lastAuth; }
}  // namespace sim_http_fetch

namespace {

const std::map<std::string, std::string> kNoHeaders;

std::string tempDir() {
  const char *base = std::getenv("TMPDIR");
  std::string dir = (base && *base) ? base : "/tmp";
  if (dir.back() != '/') dir += '/';
  dir += "crosspoint-http-dispatch-test";
  return dir;
}

void writeFile(const std::string &path, const std::string &contents) {
  std::ofstream out(path, std::ios::binary);
  out << contents;
}

// The network is the LAST resort. A fixture root, when set, must shadow it --
// that is what makes scripted QA reproducible, and it has to keep working now
// that a second transport exists.
void testMockRootWinsOverTheHostBackend() {
  const std::string dir = tempDir();
  ::system(("mkdir -p " + dir).c_str());
  writeFile(dir + "/catalog.xml", "from-mock-root");
  setenv("CROSSPOINT_SIM_HTTP_MOCK_ROOT", dir.c_str(), 1);

  const int before = sim_http_fetch::testHostCalls();
  sim_http_fetch::Response r;
  expect(sim_http_fetch::fetch("https://example.com/catalog.xml", "GET",
                               kNoHeaders, "", nullptr, r),
         "mock-root fetch succeeds");
  expect(r.body == "from-mock-root", "mock root supplied the body");
  expect(r.statusCode == 200, "mock root reports 200");
  expect(sim_http_fetch::testHostCalls() == before,
         "host backend was not reached when a fixture matched");

  unsetenv("CROSSPOINT_SIM_HTTP_MOCK_ROOT");
}

// file:// is handled in-process on every platform; it must not reach a
// transport that would have no idea what to do with the scheme.
void testFileUrlWinsOverTheHostBackend() {
  const std::string dir = tempDir();
  const std::string path = dir + "/local.txt";
  writeFile(path, "from-file-url");

  const int before = sim_http_fetch::testHostCalls();
  sim_http_fetch::Response r;
  expect(sim_http_fetch::fetch("file://" + path, "GET", kNoHeaders, "", nullptr, r),
         "file:// fetch succeeds");
  expect(r.body == "from-file-url", "file:// supplied the body");
  expect(sim_http_fetch::testHostCalls() == before,
         "host backend was not reached for file://");

  // A missing file is a 404, not a fall-through to the network.
  sim_http_fetch::Response missing;
  expect(sim_http_fetch::fetch("file://" + dir + "/nope.txt", "GET", kNoHeaders,
                               "", nullptr, missing),
         "missing file:// is still handled");
  expect(missing.statusCode == 404, "missing file:// is a 404");
  expect(sim_http_fetch::testHostCalls() == before,
         "a missing file did not fall through to the network");
}

// With no fixture, the host backend replaces curl entirely -- this is the
// branch that makes downloads work at all on a phone.
void testNetworkGoesToTheHostBackend() {
  const int before = sim_http_fetch::testHostCalls();
  sim_http_fetch::Response r;
  expect(sim_http_fetch::fetch("https://example.com/f.cpfont", "POST",
                               kNoHeaders, "user:pass", "payload", r),
         "network fetch succeeds via the host backend");
  expect(sim_http_fetch::testHostCalls() == before + 1, "host backend was called");
  expect(r.body == "from-host-backend", "host backend supplied the body");
  expect(sim_http_fetch::testLastUrl() == "https://example.com/f.cpfont",
         "url reached the backend intact");
  expect(sim_http_fetch::testLastMethod() == "POST", "method reached the backend");
  expect(sim_http_fetch::testLastAuth() == "user:pass", "basic auth reached the backend");
}

// An empty fixture root must not swallow requests: the variable being set but
// blank is what an unset shell variable expands to, and treating that as "serve
// nothing" would silently break every download.
void testEmptyMockRootIsIgnored() {
  setenv("CROSSPOINT_SIM_HTTP_MOCK_ROOT", "", 1);
  const int before = sim_http_fetch::testHostCalls();
  sim_http_fetch::Response r;
  expect(sim_http_fetch::fetch("https://example.com/x", "GET", kNoHeaders, "",
                               nullptr, r),
         "empty mock root still fetches");
  expect(sim_http_fetch::testHostCalls() == before + 1,
         "empty mock root fell through to the backend");
  unsetenv("CROSSPOINT_SIM_HTTP_MOCK_ROOT");
}

}  // namespace

int main() {
  testMockRootWinsOverTheHostBackend();
  testFileUrlWinsOverTheHostBackend();
  testNetworkGoesToTheHostBackend();
  testEmptyMockRootIsIgnored();
  ::system(("rm -rf " + tempDir()).c_str());
  std::printf("http_dispatch_test: all checks passed\n");
  return 0;
}
