/**
 * Client-side JWT payload decode, no signature verification. This is
 * intentional: the admin API re-verifies the bearer token's signature on
 * every request (app/auth/oidc.py); the SPA only needs the claims to shape
 * navigation, so decoding without verifying is not a trust boundary.
 */

function base64UrlDecode(segment: string): string {
  const base64 = segment.replace(/-/g, "+").replace(/_/g, "/");
  const paddingLength = (4 - (base64.length % 4)) % 4;
  const padded = base64 + "=".repeat(paddingLength);
  const binary = atob(padded);
  const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
  return new TextDecoder("utf-8").decode(bytes);
}

export function decodeJwtPayload(token: string): unknown {
  const segments = token.split(".");
  const payloadSegment = segments[1];
  if (segments.length < 2 || payloadSegment === undefined) {
    throw new Error("malformed JWT: missing payload segment");
  }
  return JSON.parse(base64UrlDecode(payloadSegment));
}
