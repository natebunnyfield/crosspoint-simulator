// What Speak Screen is handed for a page (src/SpokenPageText.h).
//
// THE GAP THIS WOULD HAVE CAUGHT: a page with no capturable text -- a book's
// cover wrapper, which is the first page of every book -- produced no element
// at all, so iOS reported "No speakable content could be found on the screen"
// with the whole chain healthy behind it. Owner ruling 2026-08-23: make the
// cover speak something, and make it something TRUE.
//
// Every failure mode here is silent and lands in the owner's ear: the wrong
// book's title on the right cover, the previous page's prose on a blank page,
// a title spoken OVER a page that has one word on it. None of them crash, none
// of them log, and no other test in this repo can see any of them.

#include "SpokenPageText.h"

#include <cstdio>
#include <string>
#include "TestCheck.h"
using testcheck::check;
using testcheck::checkEq;

static int &g_failures = testcheck::g_failures;

// The card's real files, copied from a live fs_ (paths and field order as the
// firmware's RecentBooksStore::toJson writes them).
static const char *kRecents =
    "{\"books\":["
    "{\"path\":\"/books/glyphs.epub\",\"title\":\"Glyph Fixture\",\"author\":\"\","
    "\"coverBmpPath\":\"/.crosspoint/epub_15990774274147839774/thumb_[HEIGHT].bmp\"},"
    "{\"path\":\"/books/wingspan-the-whole-bird.epub\",\"title\":\"Wingspan: The Whole Bird\","
    "\"author\":\"Compiled for a first-time player\",\"coverBmpPath\":\"\"},"
    "{\"path\":\"/books/measure.epub\",\"title\":\"Measure\",\"author\":\"Perf Harness\","
    "\"coverBmpPath\":\"\"}"
    "]}";

static std::string stateFor(const std::string &path) {
  return "{\"openEpubPath\":\"" + path +
         "\",\"recentSleepImages\":[0,0,0],\"recentSleepPos\":0,"
         "\"readerActivityLoadCount\":1,\"lastSleepFromReader\":true,\"showBootScreen\":true}";
}

int main() {
  using namespace spokenpage;

  // ---- 1. The card names the open book -----------------------------------
  {
    const BookIdentity id = identityForOpenBook(stateFor("/books/wingspan-the-whole-bird.epub"), kRecents);
    check(id.known(), "the open book is named");
    checkEq(id.title, "Wingspan: The Whole Bird", "title from the matching recents entry");
    checkEq(id.author, "Compiled for a first-time player", "author from the matching recents entry");
    checkEq(fallbackFor(id),
            "Wingspan: The Whole Bird. By Compiled for a first-time player. This page has no text.",
            "the spoken fallback");
  }

  // ---- 2. NOT the front entry --------------------------------------------
  //
  // The front entry is the most recently opened book, so it is usually the
  // right answer -- which is what makes guessing it dangerous. openEpubPath is
  // the only thing that says which book is on screen NOW.
  {
    const BookIdentity id = identityForOpenBook(stateFor("/books/measure.epub"), kRecents);
    checkEq(id.title, "Measure", "the entry that matches openEpubPath, not the front one");
    checkEq(id.author, "Perf Harness", "its author too");
  }

  // ---- 3. Unnamed book -> say nothing, never a guess ----------------------
  {
    // Opened from a path the recents list does not carry (imported and not yet
    // added, or a pruned entry).
    const BookIdentity absent = identityForOpenBook(stateFor("/books/nowhere.epub"), kRecents);
    check(!absent.known(), "an unmatched path names no book");
    checkEq(fallbackFor(absent), "", "an unnamed book speaks nothing");

    // Not in the reader at all.
    const BookIdentity none = identityForOpenBook(stateFor(""), kRecents);
    check(!none.known(), "no open book names no book");

    // A prefix is not a match: /books/a.epub must not answer for a.epub.bak.
    const char *near =
        "{\"books\":[{\"path\":\"/books/a.epub.bak\",\"title\":\"Backup\",\"author\":\"\"}]}";
    check(!identityForOpenBook(stateFor("/books/a.epub"), near).known(),
          "a path prefix is not a match");

    // An entry with no title cannot be named either -- the author alone is a
    // riddle, not a description of the page.
    const char *untitled =
        "{\"books\":[{\"path\":\"/books/x.epub\",\"title\":\"\",\"author\":\"Someone\"}]}";
    check(!identityForOpenBook(stateFor("/books/x.epub"), untitled).known(),
          "a titleless entry names no book");
  }

  // ---- 4. THE ROUTING: only a genuinely empty page falls back -------------
  {
    const BookIdentity id = identityForOpenBook(stateFor("/books/measure.epub"), kRecents);

    // A page with ONE WORD speaks that word. This is the supplement/substitute
    // line: the fallback replaces nothing that exists.
    checkEq(forPage("Chapter", id), "Chapter", "a one-word page speaks its word");
    checkEq(forPage("I", id), "I", "a one-letter page speaks its letter");

    // An empty capture -- the cover wrapper -- speaks the book.
    checkEq(forPage("", id), "Measure. By Perf Harness. This page has no text.",
            "an empty capture speaks the book");
    // Whitespace is not text: a page of blanks has nothing to read either.
    checkEq(forPage(" \n\t ", id), "Measure. By Perf Harness. This page has no text.",
            "a whitespace-only capture speaks the book");

    // A real page, with an unnamed book: the page still wins. The fallback is
    // never consulted when there is something to read.
    BookIdentity unknown;
    checkEq(forPage("Once upon a time", unknown), "Once upon a time",
            "a real page speaks itself even when the book is unnamed");
    checkEq(forPage("", unknown), "", "an empty page with an unnamed book speaks nothing");
  }

  // ---- 5. Punctuation, and a missing author ------------------------------
  {
    BookIdentity id;
    id.title = "Who Goes There?";
    checkEq(fallbackFor(id), "Who Goes There? This page has no text.",
            "a title that ends in punctuation is not given a second stop");
    id.title = "Middlemarch.";
    checkEq(fallbackFor(id), "Middlemarch. This page has no text.", "nor a title ending in a period");
    id.title = "Glyph Fixture";
    checkEq(fallbackFor(id), "Glyph Fixture. This page has no text.",
            "no author is no 'By' clause, not an empty one");
    id.author = "Anonymous";
    checkEq(fallbackFor(id), "Glyph Fixture. By Anonymous. This page has no text.",
            "an author is spoken as a clause");
  }

  // ---- 6. JSON that is not the shape the naive reader assumed -------------
  {
    // A quote, a backslash, a brace and the literal text of another key, all
    // inside one title. A scanner that hunts for "title" or counts braces
    // without honoring string literals gets every one of these wrong, and the
    // symptom is a mangled name read aloud.
    const char *tricky =
        "{\"books\":[{\"path\":\"/books/t.epub\","
        "\"title\":\"He said \\\"stop\\\" }, \\\"path\\\": \\\\ done\","
        "\"author\":\"A\\/B\",\"coverBmpPath\":\"\"}]}";
    const BookIdentity id = identityForOpenBook(stateFor("/books/t.epub"), tricky);
    checkEq(id.title, "He said \"stop\" }, \"path\": \\ done", "escapes and structural bytes in a title");
    checkEq(id.author, "A/B", "an escaped solidus");

    // \u escapes, including a surrogate pair: decoding the halves separately
    // would mangle any title outside the BMP.
    const char *uesc =
        "{\"books\":[{\"path\":\"/books/u.epub\",\"title\":\"Caf\\u00e9 \\ud83d\\udcd6\","
        "\"author\":\"\"}]}";
    checkEq(identityForOpenBook(stateFor("/books/u.epub"), uesc).title, "Caf\xc3\xa9 \xf0\x9f\x93\x96",
            "\\u escapes, BMP and surrogate pair");

    // Raw UTF-8 (what ArduinoJson actually writes) survives untouched.
    const char *raw =
        "{\"books\":[{\"path\":\"/books/r.epub\",\"title\":\"\xc3\x89tudes\",\"author\":\"\"}]}";
    checkEq(identityForOpenBook(stateFor("/books/r.epub"), raw).title, "\xc3\x89tudes",
            "raw UTF-8 in a title");

    // Fields this reader does not know, of every JSON type, before and after
    // the ones it does. A store that grows a field must not blank a book.
    const char *extra =
        "{\"version\":3,\"books\":[{\"lastRead\":12345,\"path\":\"/books/e.epub\","
        "\"marks\":[1,2,{\"a\":\"b\"}],\"finished\":false,\"title\":\"Grown\","
        "\"note\":null,\"author\":\"Later\"}],\"trailing\":{\"x\":1}}";
    const BookIdentity id2 = identityForOpenBook(stateFor("/books/e.epub"), extra);
    checkEq(id2.title, "Grown", "unknown fields of every type are skipped");
    checkEq(id2.author, "Later", "including around the ones we read");

    // Whitespace-formatted JSON (a hand-edited card).
    const char *pretty =
        "{\n  \"books\" : [\n    {\n      \"path\" : \"/books/p.epub\" ,\n"
        "      \"title\" : \"Pretty\" ,\n      \"author\" : \"\"\n    }\n  ]\n}\n";
    checkEq(identityForOpenBook(stateFor("/books/p.epub"), pretty).title, "Pretty",
            "pretty-printed JSON");
  }

  // ---- 7. Broken input says nothing, and never guesses --------------------
  {
    const char *broken[] = {
        "",
        "not json at all",
        "{",
        "{\"books\":",
        "{\"books\":[",
        "{\"books\":[{\"path\":\"/books/measure.epub\",\"title\":\"Trunc",
        "{\"books\":{\"path\":\"/books/measure.epub\"}}",
        "[]",
        "null",
    };
    for (const char *b : broken) {
      const BookIdentity id = identityForOpenBook(stateFor("/books/measure.epub"), b);
      check(!id.known(), "broken recents names no book");
      checkEq(forPage("", id), "", "and therefore speaks nothing");
    }
    // A broken STATE file is the same answer.
    check(!identityForOpenBook("{\"openEpubPath\":", kRecents).known(),
          "broken state names no book");
    check(!identityForOpenBook("", kRecents).known(), "empty state names no book");
  }

  // ---- 8. The list itself -------------------------------------------------
  {
    const std::vector<RecentEntry> books = parseRecents(kRecents);
    check(books.size() == 3, "every entry is parsed");
    if (books.size() == 3) {
      checkEq(books[0].path, "/books/glyphs.epub", "in file order, most recent first");
      checkEq(books[2].title, "Measure", "and the last one too");
      checkEq(books[0].author, "", "an empty author stays empty");
    }
    checkEq(topLevelString(stateFor("/books/glyphs.epub"), "openEpubPath"), "/books/glyphs.epub",
            "the open path, past the array-valued keys that follow it");
    checkEq(topLevelString(stateFor("/books/glyphs.epub"), "notAKey"), "",
            "an absent key is empty, not a guess");
  }

  if (g_failures == 0) std::printf("spoken page text: all checks passed\n");
  return g_failures == 0 ? 0 : 1;
}
