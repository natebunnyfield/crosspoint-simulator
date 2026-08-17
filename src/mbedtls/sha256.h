#pragma once

#include <cstddef>
#include <cstdint>
#include <cstring>

// mbedtls' SHA-256 surface, backed by the host's real implementation.
//
// THIS USED TO BE A FAKE, and the failure mode was the worst kind: it returned
// 32 bytes that looked like a digest and were an XOR fold of the input
// (`ctx->digest[i % 32] ^= input[i]`). Every SHA-256 the firmware computed in
// this simulator was silently wrong, would never match a real digest, and
// nothing anywhere would say so -- the same shape of defect as S-001's other
// reversals, where a stub answers confidently and incorrectly.
//
// WHAT IT ACTUALLY AFFECTS TODAY: nothing, and that is worth stating plainly
// rather than implying a fix that was not needed. The only SHA-256 caller in the
// firmware is src/network/FirmwareFlasher.cpp (the image's SHA trailer check),
// and the firmware's platformio.ini excludes that file from the `simulator`
// build -- see S-014 in BUGS.md. So this is insurance: the next caller that
// arrives gets a real digest instead of a plausible lie, and the image validator
// can be turned on without first discovering that its SHA check could never
// have passed.
//
// Host backends match MD5Builder.h's split for the same reason it has one:
// CommonCrypto on macOS, OpenSSL on Linux. Both are already linked -- macOS
// needs no extra flag and the Linux sample ini already passes -lssl -lcrypto for
// the MD5 path.
#if defined(__APPLE__)
#include <CommonCrypto/CommonDigest.h>
#elif defined(__linux__)
#include <openssl/sha.h>
#else
#error "Unsupported host OS for simulator mbedtls SHA-256"
#endif

struct mbedtls_sha256_context {
#if defined(__APPLE__)
  CC_SHA256_CTX ctx;
#else
  SHA256_CTX ctx;
#endif
  bool started = false;
};

inline void mbedtls_sha256_init(mbedtls_sha256_context *ctx) {
  if (ctx) std::memset(&ctx->ctx, 0, sizeof(ctx->ctx));
  if (ctx) ctx->started = false;
}

// is224 selects SHA-224 in mbedtls. The firmware only ever passes 0, and a
// silently-wrong 224 would be exactly the bug this file just stopped being, so
// refuse it rather than quietly hand back a SHA-256.
inline int mbedtls_sha256_starts(mbedtls_sha256_context *ctx, int is224) {
  if (!ctx) return -1;
  if (is224) return -1;  // MBEDTLS_ERR_SHA256_BAD_INPUT_DATA
#if defined(__APPLE__)
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wdeprecated-declarations"
  CC_SHA256_Init(&ctx->ctx);
#pragma clang diagnostic pop
#else
  SHA256_Init(&ctx->ctx);
#endif
  ctx->started = true;
  return 0;
}

inline int mbedtls_sha256_update(mbedtls_sha256_context *ctx, const unsigned char *input,
                                 size_t ilen) {
  if (!ctx || !ctx->started) return -1;
  if (ilen == 0) return 0;  // mbedtls treats an empty update as a no-op
  if (!input) return -1;
#if defined(__APPLE__)
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wdeprecated-declarations"
  CC_SHA256_Update(&ctx->ctx, input, static_cast<CC_LONG>(ilen));
#pragma clang diagnostic pop
#else
  SHA256_Update(&ctx->ctx, input, ilen);
#endif
  return 0;
}

inline int mbedtls_sha256_finish(mbedtls_sha256_context *ctx, unsigned char output[32]) {
  if (!output) return -1;
  if (!ctx || !ctx->started) {
    std::memset(output, 0, 32);
    return -1;
  }
#if defined(__APPLE__)
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wdeprecated-declarations"
  CC_SHA256_Final(output, &ctx->ctx);
#pragma clang diagnostic pop
#else
  SHA256_Final(output, &ctx->ctx);
#endif
  ctx->started = false;
  return 0;
}

inline void mbedtls_sha256_free(mbedtls_sha256_context *ctx) {
  if (ctx) ctx->started = false;
}
