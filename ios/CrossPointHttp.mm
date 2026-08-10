// iOS backend for sim_http_fetch: NSURLSession in place of a curl subprocess.
//
// SimHttpFetch's default transport is popen("curl ..."). That is fine on a
// developer's machine and impossible here -- iOS ships no curl binary and the
// sandbox forbids exec -- so every download path (fonts, catalogs, sync) would
// otherwise fail at the first byte. The same gap has been open on sandboxed Mac
// App Store builds, though closing it there needs a build that compiles .mm,
// which the PlatformIO desktop env does not.
//
// The contract is deliberately awkward in one specific way: fetch() is
// synchronous because HTTPClient.h and esp_http_client.h call it that way, and
// NSURLSession is not. A dispatch semaphore bridges the two. That is safe ONLY
// because firmware download paths run on FreeRTOS task threads, never on the
// SDL main thread; blocking the main thread here would deadlock against the
// completion handler if the session ever needed it, and would freeze the panel
// regardless.

#include "SimHttpFetch.h"

#import <Foundation/Foundation.h>

#include <cstring>
#include <string>

namespace sim_http_fetch {
namespace {

// NSError -> curl exit code, so failures land in the vocabulary
// simCurlExitCodeToHttpError() already speaks and the firmware's branches need
// no change. Only the codes that map to a distinct HTTPC_ERROR_* are worth
// distinguishing; everything else falls through to curl's generic 7.
int curlCodeForError(NSError *error) {
  if (!error) return 0;
  if (![error.domain isEqualToString:NSURLErrorDomain]) return 7;

  switch (error.code) {
    case NSURLErrorTimedOut:
      return 28;  // CURLE_OPERATION_TIMEDOUT -> HTTPC_ERROR_READ_TIMEOUT
    case NSURLErrorCannotFindHost:
    case NSURLErrorDNSLookupFailed:
      return 6;  // CURLE_COULDNT_RESOLVE_HOST -> HTTPC_ERROR_NO_HTTP_SERVER
    case NSURLErrorNetworkConnectionLost:
      return 56;  // CURLE_RECV_ERROR -> HTTPC_ERROR_CONNECTION_LOST
    case NSURLErrorSecureConnectionFailed:
    case NSURLErrorServerCertificateUntrusted:
    case NSURLErrorServerCertificateHasBadDate:
    case NSURLErrorServerCertificateNotYetValid:
    case NSURLErrorServerCertificateHasUnknownRoot:
      return 35;  // CURLE_SSL_CONNECT_ERROR
    default:
      return 7;  // CURLE_COULDNT_CONNECT -> HTTPC_ERROR_CONNECTION_REFUSED
  }
}

NSString *toNSString(const std::string &value) {
  return [NSString stringWithUTF8String:value.c_str()] ?: @"";
}

}  // namespace

bool hostFetch(const std::string &url, const char *method,
               const std::map<std::string, std::string> &headers,
               const std::string &basicAuth, const char *body, Response &out) {
  out = Response{};

  NSURL *nsUrl = [NSURL URLWithString:toNSString(url)];
  if (!nsUrl) {
    out.curlExitCode = 3;  // CURLE_URL_MALFORMAT
    return false;
  }

  NSMutableURLRequest *request = [NSMutableURLRequest requestWithURL:nsUrl];
  // Matches the curl backend's --connect-timeout 10 --max-time 60, so a switch
  // of transport is not also a silent switch of timeout behavior.
  request.timeoutInterval = 60.0;
  request.HTTPMethod = method && *method ? toNSString(method) : @"GET";

  for (const auto &header : headers) {
    [request setValue:toNSString(header.second)
        forHTTPHeaderField:toNSString(header.first)];
  }

  // curl -u user:pass. NSURLSession has no equivalent flag, so the header is
  // built by hand; the split is on the FIRST colon because a password may
  // legitimately contain one.
  if (!basicAuth.empty()) {
    NSData *raw = [toNSString(basicAuth) dataUsingEncoding:NSUTF8StringEncoding];
    NSString *encoded = [raw base64EncodedStringWithOptions:0];
    [request setValue:[@"Basic " stringByAppendingString:encoded]
        forHTTPHeaderField:@"Authorization"];
  }

  if (body) {
    request.HTTPBody = [NSData dataWithBytes:body length:std::strlen(body)];
  }

  __block NSData *resultData = nil;
  __block NSHTTPURLResponse *resultResponse = nil;
  __block NSError *resultError = nil;

  dispatch_semaphore_t done = dispatch_semaphore_create(0);
  NSURLSessionDataTask *task = [[NSURLSession sharedSession]
      dataTaskWithRequest:request
        completionHandler:^(NSData *data, NSURLResponse *response, NSError *error) {
          resultData = data;
          resultResponse = [response isKindOfClass:[NSHTTPURLResponse class]]
                               ? (NSHTTPURLResponse *)response
                               : nil;
          resultError = error;
          dispatch_semaphore_signal(done);
        }];
  [task resume];

  // NSURLSession redirects by default, matching curl -L.
  dispatch_semaphore_wait(done, DISPATCH_TIME_FOREVER);

  if (resultError) {
    out.curlExitCode = curlCodeForError(resultError);
    return false;
  }

  if (resultData.length > 0) {
    out.body.assign(static_cast<const char *>(resultData.bytes),
                    resultData.length);
  }
  out.statusCode = resultResponse ? static_cast<int>(resultResponse.statusCode) : 0;

  // Same success rule as the curl backend: a status line or a body counts, so a
  // legitimate 204 does not read as a transport failure.
  return out.statusCode > 0 || !out.body.empty();
}

}  // namespace sim_http_fetch
