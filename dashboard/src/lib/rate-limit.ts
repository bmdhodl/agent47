const hits = new Map<string, { count: number; resetAt: number }>();

// Clean up expired entries every 60 seconds
setInterval(() => {
  const now = Date.now();
  hits.forEach((val, key) => {
    if (now > val.resetAt) hits.delete(key);
  });
}, 60_000);

export function rateLimit(
  key: string,
  limit: number,
  windowMs: number,
): { ok: boolean; remaining: number } {
  const now = Date.now();
  const entry = hits.get(key);

  if (!entry || now > entry.resetAt) {
    hits.set(key, { count: 1, resetAt: now + windowMs });
    return { ok: true, remaining: limit - 1 };
  }

  entry.count++;

  if (entry.count > limit) {
    return { ok: false, remaining: 0 };
  }

  return { ok: true, remaining: limit - entry.count };
}

export function getClientIp(request: Request): string {
  return (
    request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ||
    request.headers.get("x-real-ip") ||
    "unknown"
  );
}
