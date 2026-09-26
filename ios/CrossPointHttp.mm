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
#include "SimHttpStream.h"

#import <Foundation/Foundation.h>

#include <cstring>
#include <memory>
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

// The request both transports send, built once so the streaming and the
// buffered paths cannot drift apart. nil when the URL does not parse.
NSMutableURLRequest *buildRequest(const std::string &url, const char *method,
                                  const std::map<std::string, std::string> &headers,
                                  const std::string &basicAuth, const char *body) {
  NSURL *nsUrl = [NSURL URLWithString:toNSString(url)];
  if (!nsUrl) return nil;
  NSMutableURLRequest *request = [NSMutableURLRequest requestWithURL:nsUrl];
  request.timeoutInterval = 60.0;  // an IDLE timeout; see hostFetch
  request.HTTPMethod = method && *method ? toNSString(method) : @"GET";
  for (const auto &header : headers) {
    [request setValue:toNSString(header.second)
        forHTTPHeaderField:toNSString(header.first)];
  }
  if (!basicAuth.empty()) {
    NSData *raw = [toNSString(basicAuth) dataUsingEncoding:NSUTF8StringEncoding];
    [request setValue:[@"Basic " stringByAppendingString:[raw base64EncodedStringWithOptions:0]]
        forHTTPHeaderField:@"Authorization"];
  }
  if (body) request.HTTPBody = [NSData dataWithBytes:body length:std::strlen(body)];
  return request;
}

}  // namespace sim_http_fetch

// The streaming delegate. One per request, owning a reference to the stream;
// the session holds the delegate strongly until it is invalidated, which
// happens when the task completes (or is cancelled by Stream::abort).
//
// Callbacks arrive on the session's own serial delegate queue -- never the
// main queue -- and didReceiveData BLOCKS there when the reader is
// kStreamCapBytes behind (Stream::push). That is the only flow control
// NSURLSession offers a data task, and it stalls only this request's queue.
@interface CrossPointHttpStreamDelegate : NSObject <NSURLSessionDataDelegate>
- (instancetype)initWithStream:(std::shared_ptr<sim_http_fetch::Stream>)stream;
@end

@implementation CrossPointHttpStreamDelegate {
  std::shared_ptr<sim_http_fetch::Stream> _stream;
}
- (instancetype)initWithStream:(std::shared_ptr<sim_http_fetch::Stream>)stream {
  if ((self = [super init])) _stream = std::move(stream);
  return self;
}
- (void)URLSession:(NSURLSession *)session
              dataTask:(NSURLSessionDataTask *)dataTask
    didReceiveResponse:(NSURLResponse *)response
     completionHandler:(void (^)(NSURLSessionResponseDisposition))completionHandler {
  // The FINAL response: NSURLSession follows redirects before this, as curl -L.
  const int status = [response isKindOfClass:[NSHTTPURLResponse class]]
                         ? static_cast<int>(((NSHTTPURLResponse *)response).statusCode)
                         : 0;
  long long len = response.expectedContentLength;  // -1 when undeclared
  // NSURLSession asks for gzip and DECODES it, while Content-Length (and so
  // expectedContentLength) counts the ENCODED bytes. Declaring that length
  // would make every compressed body read as short and fail the download, so
  // a body with a content coding declares none -- the firmware then reads to
  // the end, as it does for a chunked body. (GitHub's release JSON measured
  // arriving without a length on 2026-09-26.)
  if ([response isKindOfClass:[NSHTTPURLResponse class]]) {
    NSString *coding = [(NSHTTPURLResponse *)response valueForHTTPHeaderField:@"Content-Encoding"];
    if (coding.length > 0 && ![coding.lowercaseString isEqualToString:@"identity"]) len = -1;
  }
  _stream->setHeaders(status, len >= 0 ? static_cast<int64_t>(len) : -1);
  completionHandler(NSURLSessionResponseAllow);
}
- (void)URLSession:(NSURLSession *)session
          dataTask:(NSURLSessionDataTask *)dataTask
    didReceiveData:(NSData *)data {
  __block bool keep = true;
  [data enumerateByteRangesUsingBlock:^(const void *bytes, NSRange range, BOOL *stop) {
    if (!_stream->push(static_cast<const char *>(bytes), range.length)) {
      keep = false;
      *stop = YES;
    }
  }];
  if (!keep) [dataTask cancel];
}
- (void)URLSession:(NSURLSession *)session
                    task:(NSURLSessionTask *)task
    didCompleteWithError:(NSError *)error {
  _stream->finish(sim_http_fetch::curlCodeForError(error));
  [session finishTasksAndInvalidate];  // releases this delegate
}
@end

namespace sim_http_fetch {

bool hostOpenStream(const std::string &url, const char *method,
                    const std::map<std::string, std::string> &headers,
                    const std::string &basicAuth, const char *body,
                    const std::shared_ptr<Stream> &stream) {
  NSMutableURLRequest *request = buildRequest(url, method, headers, basicAuth, body);
  if (!request) return false;
  NSOperationQueue *queue = [[NSOperationQueue alloc] init];
  queue.maxConcurrentOperationCount = 1;  // ordered bytes
  CrossPointHttpStreamDelegate *delegate =
      [[CrossPointHttpStreamDelegate alloc] initWithStream:stream];
  NSURLSession *session =
      [NSURLSession sessionWithConfiguration:[NSURLSessionConfiguration defaultSessionConfiguration]
                                    delegate:delegate
                               delegateQueue:queue];
  NSURLSessionDataTask *task = [session dataTaskWithRequest:request];
  // Stream::abort -> cancel. The delegate's didCompleteWithError then finishes
  // the stream and invalidates the session. `task` is retained by the block.
  stream->setCancel([task]() { [task cancel]; });
  [task resume];
  return true;
}

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
  // Matches the curl backend's idle timeout (--speed-limit 1 --speed-time 60),
  // so a switch of transport is not also a silent switch of timeout behavior.
  // timeoutInterval is an IDLE timeout -- UIKit restarts it whenever data
  // arrives -- so a long download completes and only a stalled one is
  // dropped. The comment here used to say it matched `--max-time 60`, which
  // described neither side correctly: that flag capped the whole transfer and
  // this never has (S-040, the day the curl side was corrected to agree).
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
