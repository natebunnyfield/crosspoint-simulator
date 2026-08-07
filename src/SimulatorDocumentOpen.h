#pragma once

// Opening a book by double-clicking it in Finder.
//
// macOS does NOT pass the document in argv. LaunchServices sends the app an
// Apple Event ('odoc'), which SDL surfaces as SDL_EVENT_DROP_FILE -- its docs
// call that event "the system requests a file open", and it covers both the
// drag-and-drop and the open-document cases. So the path arrives asynchronously
// through the SDL event queue, not at a point of our choosing.
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
//     activity, so the process relaunches into the staged book.
//
// Bundle-only in practice (Finder is what sends 'odoc'), but nothing here is
// bundle-specific: dragging an .epub onto the window works the same way, and so
// does `open -a CrossPointX3 book.epub`.
//
// iOS is excluded. A phone has its own document story (share sheet, Files
// provider) and none of it routes through SDL_EVENT_DROP_FILE, so every entry
// point below compiles to nothing there rather than pretending to work.

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
