import { NextResponse } from "next/server";
import { authenticateApiKey, isAuthSuccess } from "@/lib/api-auth";
import { getTraceList } from "@/lib/queries";

function safeInt(val: string | null, fallback: number, min = 0, max = 500): number {
  if (!val) return fallback;
  const n = parseInt(val, 10);
  if (isNaN(n) || n < min) return fallback;
  return Math.min(n, max);
}

export async function GET(request: Request) {
  const auth = await authenticateApiKey(request);
  if (!isAuthSuccess(auth)) return auth;

  const url = new URL(request.url);
  const service = url.searchParams.get("service");
  const since = url.searchParams.get("since");
  const until = url.searchParams.get("until");

  const traces = await getTraceList(auth.teamId, {
    limit: safeInt(url.searchParams.get("limit"), 100, 1, 500),
    offset: safeInt(url.searchParams.get("offset"), 0, 0, 100000),
    service: service || undefined,
    since: since || undefined,
    until: until || undefined,
  });

  return NextResponse.json({ traces });
}
