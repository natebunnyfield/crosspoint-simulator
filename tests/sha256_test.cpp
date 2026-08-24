// The mbedtls SHA-256 shim, against published NIST/FIPS-180-4 vectors.
//
// This test exists because the shim it covers USED TO BE A FAKE: 32 bytes of
// XOR-folded input, returned with a success code. Nothing in the build could
// see that -- it has the right signature, the right output length, and it is
// deterministic, so it passes every eyeball test a digest can be given. Only a
// known-answer vector catches it, which is exactly why crypto primitives get
// known-answer tests and most other code does not.
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>

#include "mbedtls/sha256.h"
#define TESTCHECK_FATAL_DIALECT
#include "TestCheck.h"

static int &checks = testcheck::g_checks;
static std::string hexOf(const unsigned char d[32]) {
  static const char *k = "0123456789abcdef";
  std::string s;
  for (int i = 0; i < 32; i++) {
    s += k[d[i] >> 4];
    s += k[d[i] & 0xF];
  }
  return s;
}

// One-shot digest through the same call sequence FirmwareFlasher uses.
static std::string sha256Of(const void *data, size_t len) {
  mbedtls_sha256_context ctx;
  mbedtls_sha256_init(&ctx);
  CHECK(mbedtls_sha256_starts(&ctx, 0) == 0);
  CHECK(mbedtls_sha256_update(&ctx, static_cast<const unsigned char *>(data), len) == 0);
  unsigned char out[32];
  CHECK(mbedtls_sha256_finish(&ctx, out) == 0);
  mbedtls_sha256_free(&ctx);
  return hexOf(out);
}

static void testKnownVectors() {
  // FIPS-180-4 / NIST examples.
  CHECK(sha256Of("", 0) ==
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855");
  CHECK(sha256Of("abc", 3) ==
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
  CHECK(sha256Of("abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq", 56) ==
        "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1");

  // A million 'a' -- the vector that catches a buffered implementation
  // mishandling block boundaries. The old XOR fold could not have produced it
  // under any reading.
  std::string million(1000000, 'a');
  CHECK(sha256Of(million.data(), million.size()) ==
        "cdc76e5c9914fb9281a1c7e284d73e67f1809a48a497200e046d39ccc7112cd0");
}

static void testStreamingMatchesOneShot() {
  // FirmwareFlasher feeds the image in 4 KiB chunks, so a streaming digest must
  // equal the one-shot digest of the same bytes. A shim that reset state on each
  // update would pass the one-shot vectors above and fail every real file.
  std::string data;
  for (int i = 0; i < 5000; i++) data += static_cast<char>(i * 31 + 7);

  mbedtls_sha256_context ctx;
  mbedtls_sha256_init(&ctx);
  CHECK(mbedtls_sha256_starts(&ctx, 0) == 0);
  size_t off = 0;
  while (off < data.size()) {
    const size_t n = (data.size() - off < 4096) ? data.size() - off : 4096;
    CHECK(mbedtls_sha256_update(&ctx, reinterpret_cast<const unsigned char *>(data.data()) + off,
                                n) == 0);
    off += n;
  }
  unsigned char out[32];
  CHECK(mbedtls_sha256_finish(&ctx, out) == 0);
  mbedtls_sha256_free(&ctx);

  CHECK(hexOf(out) == sha256Of(data.data(), data.size()));

  // A zero-length update mid-stream is a no-op in mbedtls, and the flasher hits
  // it on a file whose size is an exact chunk multiple.
  mbedtls_sha256_context c2;
  mbedtls_sha256_init(&c2);
  CHECK(mbedtls_sha256_starts(&c2, 0) == 0);
  CHECK(mbedtls_sha256_update(&c2, reinterpret_cast<const unsigned char *>("abc"), 3) == 0);
  CHECK(mbedtls_sha256_update(&c2, nullptr, 0) == 0);
  unsigned char o2[32];
  CHECK(mbedtls_sha256_finish(&c2, o2) == 0);
  CHECK(hexOf(o2) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
}

static void testMisuseIsRefusedNotFaked() {
  // SHA-224 is a different function. Quietly returning a SHA-256 for it would
  // be the same class of lie this file was written to remove.
  mbedtls_sha256_context ctx;
  mbedtls_sha256_init(&ctx);
  CHECK(mbedtls_sha256_starts(&ctx, 1) != 0);

  // finish() without starts() must fail rather than emit a plausible digest.
  mbedtls_sha256_context fresh;
  mbedtls_sha256_init(&fresh);
  unsigned char out[32];
  std::memset(out, 0xAB, sizeof(out));
  CHECK(mbedtls_sha256_finish(&fresh, out) != 0);
  bool allZero = true;
  for (unsigned char b : out) allZero = allZero && b == 0;
  CHECK(allZero);  // zeroed, so a caller that ignores the code cannot match

  CHECK(mbedtls_sha256_update(&fresh, reinterpret_cast<const unsigned char *>("x"), 1) != 0);
}

int main() {
  testKnownVectors();
  testStreamingMatchesOneShot();
  testMisuseIsRefusedNotFaked();
  std::printf("sha256: %d checks passed\n", checks);
  return 0;
}
