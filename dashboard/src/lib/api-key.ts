import { randomBytes, createHash } from "crypto";

const PREFIX = "ag_";

export function generateApiKey(): { raw: string; hash: string; prefix: string } {
  const bytes = randomBytes(32);
  const raw = PREFIX + bytes.toString("base64url");
  const hash = hashApiKey(raw);
  const prefix = raw.slice(0, 11);
  return { raw, hash, prefix };
}

export function hashApiKey(raw: string): string {
  return createHash("sha256").update(raw).digest("hex");
}
