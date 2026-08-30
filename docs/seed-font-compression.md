# Compressed seed fonts — the CPZ1 container

*Owner ruling 2026-08-23: "compress fonts in ios app". Every number here is a
measurement taken on that date against the shipped seven-family seed tree
(`build/seedfonts`, 1x + 2x, 56 files, 117,654,860 bytes) and the build-129
IPA, unless it says otherwise.*

**Family count is stale, dated correction 2026-08-29.** The S tier grew from
seven families to **eight** on 2026-08-24, when Almendra was promoted
(`docs/trial-fonts.md`'s "The ruling (2026-08-24)"). `build/seedfonts` in this
working tree now holds Almendra, Coelacanth, Edgar, InknutJunicode,
LibreFranklin, LibrisADF, TeXGyreHeros, TeXGyreSchola — eight families,
confirmed with `find build/seedfonts -maxdepth 1 -mindepth 1 -type d`. The
byte totals in this document (117,654,860 raw, 34,837,381 CPZ1) are the
2026-08-23 seven-family measurement and have **not** been recomputed for the
eighth family — do not cite them as the current shipped size without
re-measuring against today's tree. `docs/seed-font-integrity-gate.md`
(written 2026-08-26, after the promotion) already reports "8 families" and is
the doc to check for current-state family counts.

## The gap this closes

`.cpfont` stores its 2-bit glyph bitmaps raw — `fontconvert_sdcard.py`'s own
docstring says "uncompressed 2-bit bitmaps", and measurement agrees: 108,068,437
of the tree's 117,654,860 bytes are bitmap section, at 2.448 bits/byte of
entropy and 54 % zero bytes. So the IPA's zip squeezes the whole set to
34,206,075 for the **download** and the phone expands it right back to
117,654,860 for the **install**. The install number is the one an owner with a
128 GB phone notices, and it is four times the download for no reason but the
storage format.

`ios/CrossPointFsPrep.cpp` symlinks each family from the bundle into the
emulated card rather than copying it, so the bundle copy IS the card copy and
that 117 MB is paid exactly once. It is still paid.

## What was measured, including what lost

Four ways to close it were priced before one was built.

### (a) Store deflated in the bundle, inflate at first launch — **rejected, it makes the install BIGGER**

An app bundle is read-only and permanent; nothing can delete the compressed
copy after inflating it. So the install becomes the compressed bundle **plus**
the inflated card tree:

| | install | download |
|---|---:|---:|
| today | 117,654,860 | 34,206,075 |
| (a) | 34,837,381 + 117,654,860 = **152,492,241** | 34,837,381 |

That is **+34.8 MB installed** to save nothing — it fails at the goal, before
any argument about a multi-second first launch. The symlink is what makes it
fail: if the fonts were copied rather than linked, (a) would break even, and
the copy was removed on purpose.

### (b) Store deflated, inflate on read as a stream — **rejected, the format is random-access**

`.cpfont` is seeked, not streamed, and by construction:

- `SdCardFont::load` reads the header and TOC and then *records file layout
  offsets* per style (`SdCardFont.h`, `PerStyle::intervalsFileOffset` …
  `bitmapFileOffset`).
- `prewarmStyle` sorts the page's glyphs by `dataOffset` and issues a seek per
  discontiguous run (`SdCardFont.cpp:1219`), counting them into
  `Stats::seekCount`.
- The overflow ring does an open + seek + read for a **single glyph**
  (`SdCardFont.cpp:1688`).

A deflate stream has no random access, so serving one glyph at the end of a
9.6 MB file means inflating 9.6 MB. This is not a tuning question; it is the
wrong shape.

### (c) Per-block compression inside the `.cpfont` format — **rejected on cost, not on merit**

Technically the best fit: `EpdFontData` already carries `groups`/`groupCount`
for "a DEFLATE-compressed block of glyph bitmaps" (`EpdFontData.h:141-147`),
which the builtin tables use through `FontDecompressor`, and `SdCardFont`
simply never emits or reads it. Compressing the bitmap SECTION only, in blocks,
measures:

| block | bitmaps | whole file | file ratio |
|---|---:|---:|---:|
| 8 KiB | 32,272,186 | 41,858,609 | 0.356 |
| 16 KiB | 31,139,456 | 40,725,879 | 0.346 |
| 32 KiB | 30,195,661 | 39,782,084 | 0.338 |

But it is a **format** change: `CPFONT_VERSION` bumps, `SdCardFont.cpp` is
firmware code the ESP32-C3 also compiles (where `FontDecompressor` is built for
flash-resident groups, not file-backed ones, on a 380 KB heap), and every
published font pack would need re-emitting. The ruling was about the iOS app.
Worth revisiting the day a device card needs to be smaller; not the answer to
this ask. Note also that it compresses *less* than (d) below, because it leaves
the 9.6 MB of glyph/interval/kern metadata raw.

### (d) A compressed container at the HAL's file layer — **built**

`HalFile` is the single choke point every firmware read already goes through,
and it is host-only by definition: the device has SdFat. So the container lives
there. `src/SimCompressedFile.h` sniffs four magic bytes on every read-only
open and, when they match, serves `size()`, `seek*()`, `position()`,
`available()` and `read()` from the payload's logical space, inflating one
32 KiB block at a time.

The firmware above never learns anything happened. The filename is unchanged,
so `SdCardFontRegistry` still finds `Edgar_14.cpfont` by extension and
`SdCardFontManager` still finds the companion at `<family>/2x/<same basename>`.
`size()` answers the payload's length, so WebDAV and the file-transfer screen
serve the real bytes at the real Content-Length.

| | install | download |
|---|---:|---:|
| today | 117,654,860 | 33,433,255 |
| **(d)** | **34,837,381** | 34,831,957 |

(Both download figures re-measured with one compressor over both arms — `zip -r
-9 -X` over a `Payload/` tree — so they compare to each other. The build-129 IPA
as Apple packaged it reads 34,206,075 for the same fonts.)

**−82,817,479 installed (−70.4 %)** against a download that grows by
**1,398,702 bytes (+4.2 %)**, because a container no longer compresses inside
the zip. That trade — 83 MB off the phone for 1.4 MB of download — is the whole
point.

## The format

```
offset  size            field
0       4               magic "CPZ1"
4       4               blockSize        uint32 LE, uncompressed bytes per block
8       8               originalSize     uint64 LE
16      4               blockCount       uint32 LE
20      4               reserved (0)
24      4*blockCount    blockEnd[]        cumulative compressed end offsets
24+4*bc ...             raw-deflate blocks, back to back
```

Three things about it are load-bearing:

- **`blockCount` is derived, not trusted.** `parseHeader` requires it to equal
  `ceil(originalSize / blockSize)` exactly, so a truncated or hand-edited
  container is refused at the header rather than by an out-of-range index four
  megabytes later.
- **The index is cumulative ENDs**, so a block's extent is one subtraction and
  the index carries no separate length column. Monotonicity is checked on load;
  a non-increasing pair would compute a negative length.
- **`blockSize` is a header field, not a constant on both sides.** The reader
  sizes its buffer from the file, so changing the writer's block size does not
  strand containers already written. It is bounded to [1 KiB, 1 MiB] on both
  sides — every field here is read from a file and used to size an allocation.

32 KiB is the shipped block size. Measured on the whole tree: 8 KiB → 41.9 MB,
16 KiB → 40.7 MB, 32 KiB → 39.8 MB for the bitmap-only variant, and the curve
is flat past that while the per-access inflate cost keeps rising. One block of
cache is enough because the access pattern is sorted-ascending — prewarm sorts
its reads by file offset before issuing them — so a page walks blocks forward
and touches each once.

## The failure mode is loud, and it has to be

A font that fails to load is a **blank page with successful renders in the
log** — the firmware's 2026-08-21 `OMIT_FONTS` incident, written up in
`ios/CMakeLists.txt`. So:

- A file carrying the magic whose header does not parse **fails the open**. It
  does not fall back to handing the caller container bytes as if they were font
  bytes; that is the silent version, and it surfaces as a rendering bug.
- A block that does not inflate makes `read()` return **−1**, never a short
  read. A short read looks like end of file to `SdCardFont`.
- Both say why on stderr with the `[SIM] cpz <path>: <what>` prefix, the same
  channel `HalStorage`'s own open failures use.

## Where the pieces are

| Piece | File |
|---|---|
| Format, reader, and the reasoning | [src/SimCompressedFile.h](../src/SimCompressedFile.h) |
| Transparent hook | [src/HalStorage.cpp](../src/HalStorage.cpp), `HalFile::Impl::open` and every read-path method |
| Writer | [tools/compress_seed_fonts.py](../tools/compress_seed_fonts.py) |
| Build wiring | [ios/CMakeLists.txt](../ios/CMakeLists.txt), `CROSSPOINT_IOS_COMPRESS_SEED_FONTS` (ON) |
| Test | [tests/cpz_container_test.cpp](../tests/cpz_container_test.cpp), in `tests/run_all.sh` |

The writer runs at CMake **configure** time into
`${CMAKE_BINARY_DIR}/seedfonts-cpz` (~40 s for the full tree, skipped per file
when the output is newer than its input), so it is not a step anyone has to
remember before a deploy. A failure there is `FATAL_ERROR`, not a fallback to
the raw tree: silently shipping 118 MB where 35 MB was intended is exactly the
"it built fine" class of bug the other gates in that file exist to stop.

`-DCROSSPOINT_IOS_COMPRESS_SEED_FONTS=OFF` bundles the raw tree, and it still
works because the reader sniffs per file. That is the escape hatch, and it is
also what the desktop canary exercises by default — nothing compresses
`fs_/fonts` unless someone runs the tool over it.

## What was verified

- **`tests/cpz_container_test.cpp`**, in `tests/run_all.sh` (38 passed,
  0 skipped). It drives the REAL writer through `std::system` rather than
  reimplementing its packing, because two implementations of one layout that
  agree with each other and not with the spec is the drift worth catching. It
  covers: byte-exact sequential round trip at six chunk sizes that straddle
  block boundaries; 400 random `(offset, length)` reads; a payload shorter than
  one block; reads at and past EOF; five ways a header can be inconsistent, each
  of which must fail the OPEN; a non-monotonic index; and a damaged block, which
  must not come back as a short read.
- **A real page, byte for byte.** The desktop simulator rendering
  `wingspan-the-whole-bird.epub` in LibrisADF 18 at every dial pinned off:
  two runs with the raw family and two with the same family compressed, all four
  BMPs identical. `SdCardFont` also reported the same content hash
  (`id=-632854684`) either way, which is a second, independent statement that
  the bytes reaching the loader are the same bytes.
- **Cost on the page path.** Full re-pagination (section caches dropped,
  advance tables and measure-kern rows rebuilt from the file): first page at
  8,005 ms raw against 8,267 ms compressed, with identical user CPU (2.27 s
  both) — inside the run-to-run spread. Page render itself is 1–2 ms in both
  arms.
