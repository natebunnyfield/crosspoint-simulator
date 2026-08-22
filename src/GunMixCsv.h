#pragma once

// THE GUN STORE'S CSV CODEC -- how the four-gun mixer's assignments and
// weights persist, extracted pure so a host test can see every way the store
// can lie.
//
// Two keys, written together by the iOS mixer (ios/CrossPointPaletteMixer.mm)
// and read back by it and by the desktop's settings.json (which hands
// phosphorMixBlend straight to phosphormix::mixBlend):
//
//   phosphorGunAssign  "11,40,24,21"            four preset ints, gun order
//   phosphorMixBlend   "11:50,40:50,24:50,21:0" four "preset:weight" pairs,
//                                               THE SAME gun order
//
// The load is POSITIONAL: blend pair g belongs to gun g, full stop. The preset
// field in each pair is kept for desktop compatibility (mixBlend needs it) and
// used here only as a CROSS-CHECK against the assignment. It must not be used
// as a lookup key: two guns MAY share a phosphor (weights add in linear light,
// which phosphormix::mixBlend already does), and a by-preset lookup collapses
// both guns onto whichever shared pair parses last -- the duplicated-guns bug
// this file exists to keep dead.
//
// Fallback is WHOLE, per the store's standing philosophy: a short, long,
// malformed or cross-check-failing CSV leaves the caller's arrays untouched,
// because half a stored recipe is a foreign recipe.

#include <string>

#include "PhosphorMix.h"

namespace gunmix {

constexpr int kGunCount = 4;
constexpr int kWeightMax = 100;

namespace detail {

// Parse a base-10 int spanning exactly [at, end) of s. Returns false on an
// empty or non-numeric span -- atoi's "garbage parses as 0" is how a corrupt
// pair would silently become a real weight.
inline bool parseInt(const std::string &s, size_t at, size_t end, int *out) {
  if (at >= end) return false;
  bool neg = false;
  if (s[at] == '-') { neg = true; at++; }
  if (at >= end) return false;
  long v = 0;
  for (; at < end; at++) {
    const char c = s[at];
    if (c < '0' || c > '9') return false;
    v = v * 10 + (c - '0');
    if (v > 1000000) return false;  // no stored value is near this
  }
  *out = static_cast<int>(neg ? -v : v);
  return true;
}

}  // namespace detail

// "a,b,c,d" -> four MIXABLE presets, or false with out untouched.
inline bool parseAssign(const std::string &csv, int out[kGunCount]) {
  int parsed[kGunCount];
  size_t at = 0;
  for (int g = 0; g < kGunCount; g++) {
    size_t end = csv.find(',', at);
    const bool last = end == std::string::npos;
    if (last) end = csv.size();
    if (last != (g == kGunCount - 1)) return false;  // wrong entry count
    if (!detail::parseInt(csv, at, end, &parsed[g])) return false;
    if (!phosphormix::isMixablePreset(parsed[g])) return false;
    at = end + 1;
  }
  for (int g = 0; g < kGunCount; g++) out[g] = parsed[g];
  return true;
}

// "p:w,p:w,p:w,p:w" -> four weights, POSITIONALLY, cross-checked against the
// four assigned presets. False (weights untouched) on any pair count other
// than four, a malformed pair, or a pair whose preset is not gun g's --
// that CSV was written against a different assignment and matching it up by
// preset is exactly the collapse this codec forbids. Weights clamp to
// 0..kWeightMax; 0 means that gun is off.
inline bool parseWeights(const std::string &csv, const int presets[kGunCount],
                         int out[kGunCount]) {
  int parsed[kGunCount];
  size_t at = 0;
  for (int g = 0; g < kGunCount; g++) {
    size_t end = csv.find(',', at);
    const bool last = end == std::string::npos;
    if (last) end = csv.size();
    if (last != (g == kGunCount - 1)) return false;  // wrong pair count
    const size_t colon = csv.find(':', at);
    if (colon == std::string::npos || colon >= end) return false;
    int preset = -1, weight = 0;
    if (!detail::parseInt(csv, at, colon, &preset)) return false;
    if (!detail::parseInt(csv, colon + 1, end, &weight)) return false;
    if (preset != presets[g]) return false;  // foreign recipe: fall back whole
    parsed[g] = weight < 0 ? 0 : (weight > kWeightMax ? kWeightMax : weight);
    at = end + 1;
  }
  for (int g = 0; g < kGunCount; g++) out[g] = parsed[g];
  return true;
}

inline std::string encodeAssign(const int presets[kGunCount]) {
  std::string out;
  for (int g = 0; g < kGunCount; g++) {
    if (g) out += ',';
    out += std::to_string(presets[g]);
  }
  return out;
}

inline std::string encodeBlend(const int presets[kGunCount],
                               const int w[kGunCount]) {
  std::string out;
  for (int g = 0; g < kGunCount; g++) {
    if (g) out += ',';
    out += std::to_string(presets[g]);
    out += ':';
    out += std::to_string(w[g]);
  }
  return out;
}

}  // namespace gunmix
