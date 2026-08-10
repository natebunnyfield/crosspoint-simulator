#pragma once
#include <stdint.h>

// Who owns the Return key while a firmware text field is open.
//
// Pure and SDL-free so it can be unit-tested on a host
// (tests/text_entry_enter_test.cpp). HalGPIO::update() and the level reads
// (isPressed / getHeldTime) all ask this one question, so they cannot drift
// apart -- an earlier split between the event path and the level path is
// exactly how a held letter used to read as a held button.
//
// THE PROBLEM THIS ENCODES. On hardware there are two separate inputs and no
// conflict: Confirm is a GPIO button, and a paired Bluetooth keyboard's Enter
// decodes to '\n' through the HID path (the firmware's src/notes/HidKeymap.h
// maps usage 0x28 to '\n'). The simulator collapses both onto one Return key
// on the host keyboard, so it has to choose -- and the right choice depends on
// what kind of field is open:
//
//   SINGLE-LINE (Wi-Fi password, Device owner, rename). Return is Select on
//   the on-screen keyboard, the key that types the highlighted character.
//   Committing there instead was a shipped bug: "Device Owner with daisywheel
//   does not allow character input with Select -- hitting Select exits". The
//   host typist's commit moved to Cmd/Ctrl+Return, and the on-screen keyboards
//   have their own OK key besides.
//
//   MULTI-LINE (the note editor, Claude chat). Return is a line break, which
//   is what the same key does on hardware, and there is no "commit" to
//   compete with -- a note is saved on exit, not on Return. Pressing Select
//   instead was ST-006. The panel's pick keeps a keyboard route through
//   Cmd/Ctrl+Return, so a desktop user driving the on-screen panel with the
//   arrow keys does not lose the ability to type at all.
//
// Both fields therefore keep every capability they had; only which chord
// reaches which one differs, and it differs the way the field itself does.
namespace textentry {

enum class Lines : uint8_t { Single, Multi };
enum class EnterOwner : uint8_t {
  Button, // falls through to the scancode->button map as BTN_CONFIRM
  Text,   // swallowed and queued as HalGPIO::TYPED_COMMIT ('\n')
};

inline EnterOwner enterOwner(Lines lines, bool modifierHeld) {
  if (lines == Lines::Multi) {
    return modifierHeld ? EnterOwner::Button : EnterOwner::Text;
  }
  return modifierHeld ? EnterOwner::Text : EnterOwner::Button;
}

} // namespace textentry
