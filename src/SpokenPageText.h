#pragma once

// What Speak Screen is handed for a page -- INCLUDING a page with no text on it.
//
// A book opens on its cover wrapper (an <img> and nothing else), so the
// firmware's capture is legitimately empty and every link of the chain in
// docs/speak-screen-chain.md is healthy while iOS says "No speakable content
// could be found on the screen". Owner ruling 2026-08-23: make the cover speak
// something. The cover IS the book's title and author, so saying them is a
// description of the page, not an invention. Saying anything else about a page
// nothing can read would be -- so when the book cannot be named this returns an
// empty string and iOS goes on reporting nothing, which is the truth.
//
// THE METADATA IS READ OFF THE CARD, which is why this needs no new HAL
// channel. EpubReaderActivity::onEnter writes both files before the first page
// renders: APP_STATE.saveToFile() at src/activities/reader/EpubReaderActivity.cpp:183
// puts openEpubPath in /.crosspoint/state.json, and RECENT_BOOKS.addBook() on
// the next line puts {path,title,author} at the FRONT of /.crosspoint/recent.json
// (RecentBooksStore::addBook ends in saveToFile()). So by the time any capture
// can arrive, the card already knows which book is open and what it is called.
//
// Pure, and host-tested (tests/spoken_page_text_test.cpp), for the same reason
// PanelPalette.h is: every failure mode lands in the owner's ear and nothing in
// the app can see it. Speaking the WRONG book's title is a silent lie, and the
// routing -- fall back only on an empty page, never as a supplement -- is what
// a page holding a single word would catch breaking.

#include <cstddef>
#include <string>
#include <vector>

namespace spokenpage {

struct BookIdentity {
  std::string title;
  std::string author;
  // A book with no title cannot be named, and a nameless book is nothing true
  // to say. The author alone would be a riddle, not a description.
  bool known() const { return !title.empty(); }
};

// One entry of /.crosspoint/recent.json, in the firmware's own field names.
struct RecentEntry {
  std::string path;
  std::string title;
  std::string author;
};

namespace detail {

inline void appendUtf8(unsigned cp, std::string &out) {
  if (cp < 0x80) {
    out.push_back((char)cp);
  } else if (cp < 0x800) {
    out.push_back((char)(0xC0 | (cp >> 6)));
    out.push_back((char)(0x80 | (cp & 0x3F)));
  } else if (cp < 0x10000) {
    out.push_back((char)(0xE0 | (cp >> 12)));
    out.push_back((char)(0x80 | ((cp >> 6) & 0x3F)));
    out.push_back((char)(0x80 | (cp & 0x3F)));
  } else {
    out.push_back((char)(0xF0 | (cp >> 18)));
    out.push_back((char)(0x80 | ((cp >> 12) & 0x3F)));
    out.push_back((char)(0x80 | ((cp >> 6) & 0x3F)));
    out.push_back((char)(0x80 | (cp & 0x3F)));
  }
}

inline int hexVal(char c) {
  if (c >= '0' && c <= '9') return c - '0';
  if (c >= 'a' && c <= 'f') return c - 'a' + 10;
  if (c >= 'A' && c <= 'F') return c - 'A' + 10;
  return -1;
}

// Read a \uXXXX escape body at `i` (which sits on the first hex digit).
// Advances `i` past the four digits. -1 on a malformed escape.
inline int scanHex4(const std::string &j, size_t &i) {
  if (i + 4 > j.size()) return -1;
  int v = 0;
  for (int k = 0; k < 4; k++) {
    const int h = hexVal(j[i + k]);
    if (h < 0) return -1;
    v = v * 16 + h;
  }
  i += 4;
  return v;
}

// Scan the JSON string literal at j[i] (which must be '"'), decoding escapes
// into `out` and leaving i one past the closing quote. False on a malformed
// literal, and the callers all treat that as "say nothing" -- a half-decoded
// title is a wrong title, and a wrong title is exactly the lie this file exists
// to avoid.
inline bool scanString(const std::string &j, size_t &i, std::string &out) {
  out.clear();
  if (i >= j.size() || j[i] != '"') return false;
  i++;
  while (i < j.size()) {
    const char c = j[i];
    if (c == '"') {
      i++;
      return true;
    }
    if (c != '\\') {
      out.push_back(c);
      i++;
      continue;
    }
    i++;
    if (i >= j.size()) return false;
    const char e = j[i++];
    switch (e) {
      case '"': out.push_back('"'); break;
      case '\\': out.push_back('\\'); break;
      case '/': out.push_back('/'); break;
      case 'b': out.push_back('\b'); break;
      case 'f': out.push_back('\f'); break;
      case 'n': out.push_back('\n'); break;
      case 'r': out.push_back('\r'); break;
      case 't': out.push_back('\t'); break;
      case 'u': {
        const int hi = scanHex4(j, i);
        if (hi < 0) return false;
        // A surrogate pair is two escapes for one scalar; decoding the halves
        // separately would emit two replacement-shaped sequences and mangle
        // any title outside the BMP.
        if (hi >= 0xD800 && hi <= 0xDBFF && i + 1 < j.size() && j[i] == '\\' && j[i + 1] == 'u') {
          size_t k = i + 2;
          const int lo = scanHex4(j, k);
          if (lo >= 0xDC00 && lo <= 0xDFFF) {
            i = k;
            appendUtf8(0x10000u + (((unsigned)hi - 0xD800u) << 10) + ((unsigned)lo - 0xDC00u), out);
            break;
          }
        }
        appendUtf8((unsigned)hi, out);
        break;
      }
      default:
        return false;
    }
  }
  return false;
}

inline void skipWs(const std::string &j, size_t &i) {
  while (i < j.size() && (j[i] == ' ' || j[i] == '\t' || j[i] == '\n' || j[i] == '\r')) i++;
}

// Skip any JSON value at `i`. Depth-counted and string-aware, because a title
// containing '}' or the literal text "path" must not end an object or be read
// as a key.
inline bool skipValue(const std::string &j, size_t &i) {
  skipWs(j, i);
  if (i >= j.size()) return false;
  const char c = j[i];
  if (c == '"') {
    std::string ignored;
    return scanString(j, i, ignored);
  }
  if (c == '{' || c == '[') {
    int depth = 0;
    while (i < j.size()) {
      const char d = j[i];
      if (d == '"') {
        std::string ignored;
        if (!scanString(j, i, ignored)) return false;
        continue;
      }
      if (d == '{' || d == '[') {
        depth++;
        i++;
        continue;
      }
      if (d == '}' || d == ']') {
        depth--;
        i++;
        if (depth <= 0) return depth == 0;
        continue;
      }
      i++;
    }
    return false;
  }
  // A number, true, false or null: everything up to the next structural byte.
  while (i < j.size() && j[i] != ',' && j[i] != '}' && j[i] != ']') i++;
  return true;
}

// Walk one JSON object's pairs, calling fn(key, value) for the STRING-valued
// ones and skipping the rest. `i` must sit on '{' and is left one past the
// matching '}'. Skipping unknown fields rather than refusing them is deliberate:
// a field added to the store later must not blank a book's name.
template <typename Fn>
inline bool forEachField(const std::string &j, size_t &i, Fn fn) {
  skipWs(j, i);
  if (i >= j.size() || j[i] != '{') return false;
  i++;
  skipWs(j, i);
  if (i < j.size() && j[i] == '}') {
    i++;
    return true;
  }
  while (i < j.size()) {
    skipWs(j, i);
    std::string key;
    if (!scanString(j, i, key)) return false;
    skipWs(j, i);
    if (i >= j.size() || j[i] != ':') return false;
    i++;
    skipWs(j, i);
    if (i < j.size() && j[i] == '"') {
      std::string value;
      if (!scanString(j, i, value)) return false;
      fn(key, value);
    } else if (!skipValue(j, i)) {
      return false;
    }
    skipWs(j, i);
    if (i < j.size() && j[i] == ',') {
      i++;
      continue;
    }
    if (i < j.size() && j[i] == '}') {
      i++;
      return true;
    }
    return false;
  }
  return false;
}

inline std::string trim(const std::string &s) {
  size_t b = 0, e = s.size();
  auto space = [](char c) { return c == ' ' || c == '\t' || c == '\n' || c == '\r'; };
  while (b < e && space(s[b])) b++;
  while (e > b && space(s[e - 1])) e--;
  return s.substr(b, e - b);
}

// End a clause without doubling the punctuation a title already carries.
inline void endSentence(std::string &s) {
  if (s.empty()) return;
  const char c = s.back();
  if (c == '.' || c == '!' || c == '?') return;
  s.push_back('.');
}

}  // namespace detail

// The value of a top-level STRING key; "" when it is absent, non-string, or the
// document does not parse. Every one of those means the same thing to a caller:
// the card did not tell us, so say nothing.
inline std::string topLevelString(const std::string &json, const std::string &key) {
  size_t i = 0;
  std::string found;
  detail::forEachField(json, i, [&](const std::string &k, const std::string &v) {
    if (k == key && found.empty()) found = v;
  });
  return found;
}

// The recents list, in the file's own order (the firmware keeps it most-recent
// first). An empty vector on anything unexpected.
inline std::vector<RecentEntry> parseRecents(const std::string &json) {
  std::vector<RecentEntry> out;
  size_t i = 0;
  detail::skipWs(json, i);
  if (i >= json.size() || json[i] != '{') return out;
  i++;
  while (i < json.size()) {
    detail::skipWs(json, i);
    if (i < json.size() && json[i] == '}') return out;
    std::string key;
    if (!detail::scanString(json, i, key)) return out;
    detail::skipWs(json, i);
    if (i >= json.size() || json[i] != ':') return out;
    i++;
    detail::skipWs(json, i);
    if (key == "books" && i < json.size() && json[i] == '[') {
      i++;
      while (i < json.size()) {
        detail::skipWs(json, i);
        if (i >= json.size()) return out;
        if (json[i] == ']') return out;
        if (json[i] != '{') return out;
        RecentEntry e;
        if (!detail::forEachField(json, i, [&](const std::string &k, const std::string &v) {
              if (k == "path") e.path = v;
              else if (k == "title") e.title = v;
              else if (k == "author") e.author = v;
            }))
          return out;
        out.push_back(e);
        detail::skipWs(json, i);
        if (i < json.size() && json[i] == ',') {
          i++;
          continue;
        }
        return out;  // ']' or a malformed tail: the list we have is the list.
      }
      return out;
    }
    if (!detail::skipValue(json, i)) return out;
    detail::skipWs(json, i);
    if (i < json.size() && json[i] == ',') {
      i++;
      continue;
    }
    return out;
  }
  return out;
}

// Who wrote the book that is open right now, from the two files the card
// already holds. An unknown identity is the normal answer outside the reader.
//
// NO GUESSING. The recents entry must match openEpubPath exactly. The FRONT
// entry is the most recently opened book and would usually be the right one,
// which is precisely what makes it dangerous: "usually right" here means
// occasionally speaking another book's title over this one's cover, and nothing
// in the app or its logs could ever see that happen.
inline BookIdentity identityForOpenBook(const std::string &stateJson,
                                        const std::string &recentJson) {
  BookIdentity id;
  const std::string open = detail::trim(topLevelString(stateJson, "openEpubPath"));
  if (open.empty()) return id;
  for (const RecentEntry &e : parseRecents(recentJson)) {
    if (detail::trim(e.path) != open) continue;
    id.title = detail::trim(e.title);
    id.author = detail::trim(e.author);
    break;
  }
  return id;
}

// What to speak on a page with nothing to read. Empty when the book cannot be
// named -- iOS then reports "no speakable content", which is then the truth.
//
// The closing sentence is what keeps this honest on a page that is NOT the
// cover. Nothing reachable here says which page this is (the channel carries
// text and rects, and on such a page there are neither), so the words say only
// what IS known: which book this is, and that this page has no text on it. A
// blank interior page or a dropped illustration therefore gets a true sentence
// rather than an implied cover.
inline std::string fallbackFor(const BookIdentity &id) {
  if (!id.known()) return std::string();
  std::string s = id.title;
  detail::endSentence(s);
  if (!id.author.empty()) {
    s += " By ";
    s += id.author;
    detail::endSentence(s);
  }
  s += " This page has no text.";
  return s;
}

// THE ROUTING, and the whole of the bug. An empty capture used to route to no
// element at all; it now routes to the book. A page holding a SINGLE WORD
// routes to that word -- the fallback is a substitute for nothing, never a
// supplement to something.
inline std::string forPage(const std::string &pageUtf8, const BookIdentity &id) {
  for (unsigned char c : pageUtf8) {
    if (c > 0x20) return pageUtf8;
  }
  return fallbackFor(id);
}

}  // namespace spokenpage
