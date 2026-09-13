#pragma once
//
// A STAND-IN <curl/curl.h> FOR TESTING SimHttpFetch.h's libcurl branch.
//
// That branch only compiles on macOS (CROSSPOINT_SIM_LIBCURL), and the machines
// that most often run this suite are Linux ones with no libcurl headers at all.
// Without this, the branch would ship with nothing exercising it -- the same
// gap the iOS hostFetch branch has a note about.
//
// It is deliberately NOT a network stub: it records every option the code sets
// and replays a scripted outcome, so the test can assert the REQUEST WAS BUILT
// CORRECTLY rather than merely that something was returned. That is the half a
// live server could not check anyway.
//
// WHAT IT DOES NOT PROVE: that the real headers declare these the same way.
// The signatures here are written from libcurl's documented API, and a mismatch
// (a wrong option name, a long where curl wants a pointer) would compile here
// and fail on a Mac. Treat a pass as "the logic and the option set are right",
// not "this links against real libcurl".

#include <cstdarg>
#include <cstring>
#include <string>
#include <vector>

typedef void CURL;

typedef enum {
  CURLE_OK = 0,
  CURLE_COULDNT_CONNECT = 7,
  CURLE_OPERATION_TIMEDOUT = 28,
  CURLE_GOT_NOTHING = 52,
} CURLcode;

#define CURL_GLOBAL_DEFAULT 3L
#define CURLAUTH_BASIC 1L

typedef enum {
  CURLOPT_URL = 10002,
  CURLOPT_WRITEFUNCTION = 20011,
  CURLOPT_WRITEDATA = 10001,
  CURLOPT_FOLLOWLOCATION = 52,
  CURLOPT_CONNECTTIMEOUT = 78,
  CURLOPT_LOW_SPEED_LIMIT = 19,
  CURLOPT_LOW_SPEED_TIME = 20,
  CURLOPT_NOSIGNAL = 99,
  CURLOPT_CUSTOMREQUEST = 10036,
  CURLOPT_HTTPHEADER = 10023,
  CURLOPT_HTTPAUTH = 107,
  CURLOPT_USERPWD = 10005,
  CURLOPT_COPYPOSTFIELDS = 10165,
} CURLoption;

typedef enum {
  CURLINFO_RESPONSE_CODE = 2097154,
} CURLINFO;

struct curl_slist {
  char *data;
  struct curl_slist *next;
};

typedef size_t (*mock_curl_write_cb)(char *, size_t, size_t, void *);

// Everything the code under test did, and what it should get back.
struct MockCurl {
  // Recorded request.
  std::string url;
  std::string customRequest;
  std::string userpwd;
  std::string postFields;
  std::vector<std::string> headers;
  long followLocation = -1;
  long connectTimeout = -1;
  long lowSpeedLimit = -1;
  long lowSpeedTime = -1;
  long noSignal = -1;
  long httpAuth = -1;
  bool hadWriteFunction = false;
  bool slistFreed = false;
  bool cleanedUp = false;
  int globalInits = 0;
  int easyInits = 0;

  // Scripted outcome.
  CURLcode performResult = CURLE_OK;
  long responseCode = 200;
  std::string responseBody;
  bool failEasyInit = false;

  mock_curl_write_cb writeCb = nullptr;
  void *writeData = nullptr;

  void reset() { *this = MockCurl(); }
};

inline MockCurl &mockCurl() {
  static MockCurl state;
  return state;
}

inline CURLcode curl_global_init(long) {
  mockCurl().globalInits++;
  return CURLE_OK;
}

inline CURL *curl_easy_init() {
  mockCurl().easyInits++;
  if (mockCurl().failEasyInit)
    return nullptr;
  static int handle = 0;
  return &handle;
}

inline CURLcode curl_easy_setopt(CURL *, CURLoption option, ...) {
  va_list ap;
  va_start(ap, option);
  MockCurl &m = mockCurl();
  switch (option) {
  case CURLOPT_URL: m.url = va_arg(ap, const char *); break;
  case CURLOPT_CUSTOMREQUEST: m.customRequest = va_arg(ap, const char *); break;
  case CURLOPT_USERPWD: m.userpwd = va_arg(ap, const char *); break;
  case CURLOPT_COPYPOSTFIELDS: m.postFields = va_arg(ap, const char *); break;
  case CURLOPT_FOLLOWLOCATION: m.followLocation = va_arg(ap, long); break;
  case CURLOPT_CONNECTTIMEOUT: m.connectTimeout = va_arg(ap, long); break;
  case CURLOPT_LOW_SPEED_LIMIT: m.lowSpeedLimit = va_arg(ap, long); break;
  case CURLOPT_LOW_SPEED_TIME: m.lowSpeedTime = va_arg(ap, long); break;
  case CURLOPT_NOSIGNAL: m.noSignal = va_arg(ap, long); break;
  case CURLOPT_HTTPAUTH: m.httpAuth = va_arg(ap, long); break;
  case CURLOPT_WRITEFUNCTION:
    m.writeCb = va_arg(ap, mock_curl_write_cb);
    m.hadWriteFunction = true;
    break;
  case CURLOPT_WRITEDATA: m.writeData = va_arg(ap, void *); break;
  case CURLOPT_HTTPHEADER: {
    auto *list = va_arg(ap, struct curl_slist *);
    for (; list; list = list->next)
      m.headers.push_back(list->data);
    break;
  }
  }
  va_end(ap);
  return CURLE_OK;
}

inline struct curl_slist *curl_slist_append(struct curl_slist *list,
                                            const char *value) {
  auto *node = new curl_slist{strdup(value), nullptr};
  if (!list)
    return node;
  struct curl_slist *tail = list;
  while (tail->next)
    tail = tail->next;
  tail->next = node;
  return list;
}

inline void curl_slist_free_all(struct curl_slist *list) {
  if (list)
    mockCurl().slistFreed = true;
  while (list) {
    struct curl_slist *next = list->next;
    free(list->data);
    delete list;
    list = next;
  }
}

// Replays the scripted body through the write callback exactly as libcurl
// would, so the code's own accumulation is what produces Response::body.
inline CURLcode curl_easy_perform(CURL *) {
  MockCurl &m = mockCurl();
  if (m.writeCb && !m.responseBody.empty()) {
    m.writeCb(const_cast<char *>(m.responseBody.data()), 1,
              m.responseBody.size(), m.writeData);
  }
  return m.performResult;
}

inline CURLcode curl_easy_getinfo(CURL *, CURLINFO info, ...) {
  va_list ap;
  va_start(ap, info);
  if (info == CURLINFO_RESPONSE_CODE)
    *va_arg(ap, long *) = mockCurl().responseCode;
  va_end(ap);
  return CURLE_OK;
}

inline void curl_easy_cleanup(CURL *) { mockCurl().cleanedUp = true; }
