// SimHttpFetch.h's libcurl branch: the request it builds and the Response it
// returns.
//
// Why this exists: the branch compiles only on macOS, and the machines that run
// this suite are usually Linux. CROSSPOINT_SIM_LIBCURL is forced on here and
// tests/mock_curl/ supplies a <curl/curl.h> that records options and replays a
// scripted outcome, so the branch is exercised everywhere the suite runs.
//
// The request assertions are the point. A live server could show that a fetch
// works; only this can show that -L, the IDLE timeout pair, NOSIGNAL and the
// auth/method/header plumbing are actually set -- and the idle timeout in
// particular is a regression that already shipped once on the subprocess side
// (see curlCommand's note: --max-time killed healthy downloads at 60 s).
//
// What it does NOT prove: that real libcurl declares these the same way. The
// mock is written from the documented API; a mismatch compiles here and fails
// on a Mac.

#define CROSSPOINT_SIM_LIBCURL 1

#include "../src/SimHttpFetch.h"

#include "TestCheck.h"

#include <cstdio>

using testcheck::check;
using testcheck::checkEq;

namespace {

sim_http_fetch::Response run(const char *method,
                             const std::map<std::string, std::string> &headers,
                             const std::string &basicAuth, const char *body) {
  sim_http_fetch::Response out;
  sim_http_fetch::fetch("https://example.invalid/feed.xml", method, headers,
                        basicAuth, body, out);
  return out;
}

void theOptionsEveryRequestSets() {
  mockCurl().reset();
  mockCurl().responseBody = "hello";
  sim_http_fetch::Response out = run("GET", {}, "", nullptr);

  checkEq(mockCurl().url, std::string("https://example.invalid/feed.xml"),
          "the URL is passed through");
  checkEq(mockCurl().followLocation, 1L, "-L: redirects are followed");
  checkEq(mockCurl().connectTimeout, 10L, "--connect-timeout 10");
  // The pair that makes the timeout IDLE rather than total.
  checkEq(mockCurl().lowSpeedLimit, 1L, "--speed-limit 1");
  checkEq(mockCurl().lowSpeedTime, 60L, "--speed-time 60");
  check(mockCurl().noSignal == 1L, "NOSIGNAL is set: callers are off-thread");
  check(mockCurl().hadWriteFunction, "a write callback is installed");

  checkEq(out.body, std::string("hello"), "the body comes back through the callback");
  checkEq(out.statusCode, 200, "the status comes from CURLINFO_RESPONSE_CODE");
  checkEq(out.curlExitCode, 0, "CURLE_OK is exit code 0");
  check(mockCurl().cleanedUp, "the easy handle is cleaned up");
}

void aPlainGetSetsNoMethodNoAuthNoBody() {
  mockCurl().reset();
  run("GET", {}, "", nullptr);
  check(mockCurl().customRequest.empty(),
        "GET does not set CUSTOMREQUEST -- that is curl's default");
  check(mockCurl().userpwd.empty(), "no auth means no USERPWD");
  check(mockCurl().postFields.empty(), "no body means no POSTFIELDS");
  check(mockCurl().httpAuth == -1, "no auth means HTTPAUTH is untouched");
}

void methodHeadersAuthAndBody() {
  mockCurl().reset();
  run("PUT", {{"Accept", "application/json"}, {"X-Trace", "7"}}, "user:pass",
      "{\"a\":1}");

  checkEq(mockCurl().customRequest, std::string("PUT"), "a non-GET method is set");
  checkEq(mockCurl().userpwd, std::string("user:pass"), "basic auth is passed as USERPWD");
  checkEq(mockCurl().httpAuth, CURLAUTH_BASIC, "and selects basic auth");
  checkEq(mockCurl().postFields, std::string("{\"a\":1}"), "the body is copied in");
  checkEq(mockCurl().headers.size(), size_t(2), "both headers are sent");
  checkEq(mockCurl().headers[0], std::string("Accept: application/json"),
          "headers are formatted 'Name: value'");
  checkEq(mockCurl().headers[1], std::string("X-Trace: 7"), "and all of them arrive");
  check(mockCurl().slistFreed, "the header list is freed");
}

// The mapping these codes feed is simCurlExitCodeToHttpError(), which switches
// on curl's CLI exit numbers. CURLcode uses those same numbers, which is the
// reason this swap does not disturb the firmware's error handling.
void failuresReportCurlsOwnCode() {
  mockCurl().reset();
  mockCurl().performResult = CURLE_COULDNT_CONNECT;
  mockCurl().responseCode = 0;
  sim_http_fetch::Response out = run("GET", {}, "", nullptr);
  checkEq(out.curlExitCode, 7, "CURLE_COULDNT_CONNECT is 7, as the CLI exits 7");
  checkEq(out.statusCode, 0, "no status when the connection never happened");

  mockCurl().reset();
  mockCurl().performResult = CURLE_OPERATION_TIMEDOUT;
  mockCurl().responseCode = 0;
  out = run("GET", {}, "", nullptr);
  checkEq(out.curlExitCode, 28, "CURLE_OPERATION_TIMEDOUT is 28");
}

// A 404 is a completed transfer, not a failure: the old path returned it and
// the callers branch on statusCode.
void anHttpErrorStatusIsStillASuccessfulFetch() {
  mockCurl().reset();
  mockCurl().responseCode = 404;
  mockCurl().responseBody = "nope";
  sim_http_fetch::Response out;
  const bool ok = sim_http_fetch::fetch("https://example.invalid/missing", "GET",
                                        {}, "", nullptr, out);
  check(ok, "a 404 is reported as a completed fetch");
  checkEq(out.statusCode, 404, "with its status");
  checkEq(out.body, std::string("nope"), "and its body");
}

void globalInitHappensOnceAcrossManyFetches() {
  // reset() zeroes the counter but the function-local static stays initialised,
  // so a second call must NOT init again.
  mockCurl().reset();
  run("GET", {}, "", nullptr);
  run("GET", {}, "", nullptr);
  run("GET", {}, "", nullptr);
  checkEq(mockCurl().globalInits, 0,
          "curl_global_init already ran in an earlier test and does not repeat");
  checkEq(mockCurl().easyInits, 3, "but each fetch gets its own easy handle");
}

void aRefusedHandleFailsRatherThanCrashing() {
  mockCurl().reset();
  mockCurl().failEasyInit = true;
  sim_http_fetch::Response out;
  const bool ok = sim_http_fetch::fetch("https://example.invalid/x", "GET", {},
                                        "", nullptr, out);
  check(!ok, "a null easy handle is a failed fetch, not a dereference");
}

// The mock root and file:// shortcuts sit AHEAD of any transport and must keep
// doing so, or scripted QA stops working on the Mac the day it switches.
void fileUrlsNeverReachTheTransport() {
  mockCurl().reset();
  sim_http_fetch::Response out;
  sim_http_fetch::fetch("file:///definitely/not/here", "GET", {}, "", nullptr, out);
  checkEq(mockCurl().easyInits, 0, "a file:// URL does not open a curl handle");
}

} // namespace

int main() {
  theOptionsEveryRequestSets();
  aPlainGetSetsNoMethodNoAuthNoBody();
  methodHeadersAuthAndBody();
  failuresReportCurlsOwnCode();
  anHttpErrorStatusIsStillASuccessfulFetch();
  globalInitHappensOnceAcrossManyFetches();
  aRefusedHandleFailsRatherThanCrashing();
  fileUrlsNeverReachTheTransport();

  if (testcheck::g_failures == 0)
    printf("sim_libcurl: all checks passed\n");
  return testcheck::g_failures == 0 ? 0 : 1;
}
