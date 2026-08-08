// P0 (2026-08-08): the web-server dispatch handoff must signal the parked
// worker on EVERY exit from the handler, including an exception.
//
// WebServer's accept worker parses a request, parks it behind a condition
// variable, and waits for handleClient() (on the firmware thread) to drain it
// and set dispatchDone. The signal was a trailing statement after the handler
// call, so a handler that threw skipped it and the worker waited forever -- one
// std::bad_alloc under memory pressure and the whole file-transfer server hung
// with no recovery. This TU builds with exceptions, as the real one does.
//
// This pins the pattern, not the socket code: a worker parked on the same CV
// contract, a drain that invokes a throwing callback, and the requirement that
// the worker still wakes. The "old" form is included so the test is red against
// the bug it guards.

#include <atomic>
#include <cassert>
#include <chrono>
#include <condition_variable>
#include <cstdio>
#include <mutex>
#include <stdexcept>
#include <thread>

namespace {

struct Channel {
  std::mutex m;
  std::condition_variable cv;
  bool pending = false;
  bool done = false;
};

// Park like the accept worker: publish the request, wait for done. Returns
// whether it woke within the timeout (false == the hang).
bool workerParks(Channel &ch, std::chrono::milliseconds limit) {
  std::unique_lock<std::mutex> lock(ch.m);
  ch.pending = true;
  ch.done = false;
  ch.cv.notify_all();
  return ch.cv.wait_for(lock, limit, [&ch] { return ch.done; });
}

// THE FIX: signal from a scope guard, so it fires on normal return and on
// exception unwind alike.
template <typename Handler>
void drainWithGuard(Channel &ch, Handler handler) {
  {
    std::unique_lock<std::mutex> lock(ch.m);
    if (!ch.pending) return;
    ch.pending = false;
  }
  struct Signal {
    Channel *ch;
    ~Signal() {
      std::lock_guard<std::mutex> lock(ch->m);
      ch->done = true;
      ch->cv.notify_all();
    }
  } signal{&ch};
  handler();
}

// THE OLD FORM, kept only to prove the test can see the bug: signal as a
// trailing statement, skipped when the handler throws.
template <typename Handler>
void drainTrailing(Channel &ch, Handler handler) {
  {
    std::unique_lock<std::mutex> lock(ch.m);
    if (!ch.pending) return;
    ch.pending = false;
  }
  handler();
  std::lock_guard<std::mutex> lock(ch.m);
  ch.done = true;
  ch.cv.notify_all();
}

template <typename Drain>
bool survivesThrow(Drain drain) {
  Channel ch;
  std::atomic<bool> woke{false};
  std::thread worker([&] { woke = workerParks(ch, std::chrono::milliseconds(400)); });
  // Let the worker park before draining.
  std::this_thread::sleep_for(std::chrono::milliseconds(20));
  try {
    drain(ch, [] { throw std::runtime_error("handler blew up"); });
  } catch (...) {
    // handleClient lets it propagate; the point is the worker still woke.
  }
  worker.join();
  return woke;
}

}  // namespace

int main() {
  // Precondition: the OLD form really does hang on a throw. If this ever starts
  // passing, the test has stopped exercising the bug and needs rewriting.
  assert(!survivesThrow([](Channel &ch, auto h) { drainTrailing(ch, h); }) &&
         "the trailing-statement form must hang on a throwing handler -- "
         "otherwise this test proves nothing");

  // The fix: the worker wakes even though the handler threw.
  assert(survivesThrow([](Channel &ch, auto h) { drainWithGuard(ch, h); }) &&
         "the scope-guard form must release the parked worker on a throw");

  // And it still works on the normal path.
  {
    Channel ch;
    std::atomic<bool> woke{false};
    std::thread worker([&] { woke = workerParks(ch, std::chrono::milliseconds(400)); });
    std::this_thread::sleep_for(std::chrono::milliseconds(20));
    drainWithGuard(ch, [] { /* ordinary handler */ });
    worker.join();
    assert(woke && "the guard must also signal on a normal return");
  }

  std::puts("dispatch_signal: PASS");
  return 0;
}
