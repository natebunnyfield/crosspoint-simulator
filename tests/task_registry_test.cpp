// FreeRTOS shim: the task registry must not outlive the handle it points at.
//
// THE BUG THIS EXISTS FOR
//
// xTaskCreate() dedupes by task name -- deliberately, because the iOS
// in-process reboot re-runs setup() without tearing the process down, and a
// second xTaskCreate for "render" would otherwise spawn a second render thread
// and orphan the first, leaving two threads writing one framebuffer.
//
// vTaskDelete() freed the handle but left the registry entry pointing at it. So
// the create/delete/create sequence -- which is exactly what the reboot path
// does -- took the dedupe branch and handed the caller freed memory. The next
// xTaskNotify() on it is a use-after-free: heap corruption or a hang, arriving
// far from the delete that caused it.
//
// WHY THE ASSERTION IS BEHAVIOURAL AND NOT `b != a`
//
// Pointer identity proves nothing here: the allocator reuses the just-freed
// block, so a correct implementation frequently returns the SAME address for
// the new handle. The first version of this test asserted `b != a` and failed
// against the fixed code. What actually distinguishes the two is whether a
// thread was spawned at all -- on the stale-dedupe path xTaskCreate returns
// early and never runs the body.
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include <atomic>
#include <chrono>
#include <cstdio>
#include <thread>

namespace {

std::atomic<int> gRan{0};
void body(void *) { gRan.fetch_add(1); }

int failures = 0;
void check(bool cond, const char *what) {
  if (!cond) {
    std::printf("FAIL: %s\n", what);
    failures++;
  }
}

// The shim's threads are real OS threads, so give them a moment to be
// scheduled. Generous on purpose: a slow CI box must not read as a red test.
void settle() { std::this_thread::sleep_for(std::chrono::milliseconds(200)); }

}  // namespace

int main() {
  TaskHandle_t first = nullptr;
  xTaskCreate(body, "render", 4096, nullptr, 1, &first);
  settle();
  check(first != nullptr, "xTaskCreate returned a handle");
  check(gRan.load() == 1, "the first task body ran");

  // The dedupe branch itself is load-bearing -- prove it still fires while the
  // task is alive, or the fix below would have been "delete the dedupe".
  TaskHandle_t duplicate = nullptr;
  xTaskCreate(body, "render", 4096, nullptr, 1, &duplicate);
  settle();
  check(duplicate == first, "a live task is deduped by name, not respawned");
  check(gRan.load() == 1, "dedupe did not spawn a second thread");

  vTaskDelete(first);

  TaskHandle_t second = nullptr;
  xTaskCreate(body, "render", 4096, nullptr, 1, &second);
  settle();
  check(second != nullptr, "re-create returned a handle");
  check(gRan.load() == 2, "re-create after delete spawned a REAL task (stale registry entry)");
  vTaskDelete(second);

  if (failures == 0) {
    std::printf("task_registry_test: all checks passed\n");
    return 0;
  }
  std::printf("task_registry_test: %d check(s) failed\n", failures);
  return 1;
}
