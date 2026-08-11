#pragma once

// Opening a book handed to us by the OS: double-clicked in Finder on desktop,
// or tapped in Files/Mail/AirDrop/the Share Sheet on iOS.
//
// Neither platform passes the document in argv. macOS LaunchServices sends the
// app an Apple Event ('odoc'); iOS UIKit calls the app delegate's
// application:openURL:options: (cold launch) or scene:openURLContexts: (warm).
// SDL's AppKit and UIKit backends both fold their case into the same call --
// SDL_SendDropFile -- so both surface here as SDL_EVENT_DROP_FILE. Verified
// against the vendored SDL3 source (release-3.4.12):
// src/video/uikit/SDL_uikitappdelegate.m's -handleURL: is the iOS counterpart
// of the Cocoa 'odoc' handler and calls the identical SDL function. So the path
// arrives asynchronously through the SDL event queue on both platforms, not at
// a point of our choosing, and nothing below is platform-specific.
//
// What this module does with it: copy the book onto the simulated SD card under
// /books and record it as APP_STATE.openEpubPath. No new firmware entry point is
// needed for that -- main.cpp's boot routing already opens openEpubPath, which
// is the same mechanism that makes the device come up in the book you were last
// reading. The simulator only has to have written that state before setup()
// reads it.
//
// Hence two paths, and the difference is purely about timing relative to
// setup():
//   - launch open: the event arrives before setup(), so staging it is enough
//     and the book is on screen at the first paint.
//   - warm open: the app is already running and setup() has long since chosen an
//     activity, so the process relaunches into the staged book. On iOS that
//     relaunch is SimulatorLifecycle::rebootForDocumentOpen()'s in-process
//     longjmp -- the sandbox forbids the execvp() desktop uses.
//
// Bundle-only in practice, but nothing here is bundle-specific: dragging an
// .epub onto the desktop window works the same way, and so does
// `open -a CrossPointX3 book.epub`.
//
// iOS document delivery is assumed to land as a real copy under the app's
// sandbox (Inbox-style import), which is what a plain CFBundleDocumentTypes
// declaration with no UIDocumentBrowser support gets from iOS in practice --
// so the plain POSIX read below needs no security-scoped-resource dance. Not
// yet confirmed against a genuine Files "Open In Place" source; see ios/README.md.

namespace SimulatorDocumentOpen {

// Call before setup(), from main().
//
// Initialises SDL early so there is an event queue to receive the launch
// document at all -- SDL_Init is refcounted, so HalDisplay::begin()'s own call
// still pairs correctly with the single SDL_Quit() at the end of main(). Then it
// installs the event watch and waits briefly for LaunchServices to deliver.
//
// Returns as soon as a document arrives, so the wait costs nothing on the launch
// that has one. A launch with no document pays the full (short) timeout once.
void captureLaunchDocument();

// Call once per frame from main()'s loop.
//
// Acts on a document opened while the app is already running: stages it and
// relaunches, because the firmware picks its activity during setup() and there
// is no in-process "open this book now" entry point to call instead.
void pumpPendingOpen();

}  // namespace SimulatorDocumentOpen
