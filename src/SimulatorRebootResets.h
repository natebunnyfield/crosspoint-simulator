#pragma once

#include <functional>
#include <vector>

// Process-scoped state that must be re-initialised when the simulator "reboots"
// WITHOUT starting a new process.
//
// The desktop reboot is execvp: a genuinely fresh process, so every static goes
// back to its initial value for free. iOS cannot exec inside the sandbox, so its
// reboot is a longjmp back into setup() in the SAME process -- and there,
// anything guarded by a `static bool ...Initialized` stays initialised, so the
// re-read never happens. The result is that a feature works on the desktop, is
// dead on the phone, and the two disagree silently.
//
// That bit `rebootAsPowerWake()`, which promotes the *_AFTER_WAKE schedules on
// every reboot: the promotion was real, but the consumers had already latched
// their env-derived state and never looked again. Dead code on the only platform
// that uses the path.
//
// Modules register a reset here; SimulatorLifecycle runs them immediately before
// the jump. Registration is via a namespace-scope object in each .cpp, and the
// registry is a function-local static so there is no static-initialisation-order
// dependency between them.
namespace simreset {

inline std::vector<std::function<void()>> &registry() {
  static std::vector<std::function<void()>> fns;
  return fns;
}

inline void add(std::function<void()> fn) { registry().push_back(std::move(fn)); }

inline void runAll() {
  for (auto &fn : registry()) fn();
}

// Helper for the common `static Registrar r{[]{ ... }};` shape.
struct Registrar {
  explicit Registrar(std::function<void()> fn) { add(std::move(fn)); }
};

}  // namespace simreset
