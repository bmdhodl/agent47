import { NextResponse } from "next/server";
import { authenticateApiKey, isAuthSuccess } from "@/lib/api-auth";
import { getAlerts } from "@/lib/queries";

function safeInt(val: string | null, fallback: number, min = 0, max = 200): number {
  if (!val) return fallback;
  const n = parseInt(val, 10);
  if (isNaN(n) || n < min) return fallback;
  return Math.min(n, max);
}

export async function GET(request: Request) {
  const auth = await authenticateApiKey(request);
  if (!isAuthSuccess(auth)) return auth;

  const url = new URL(request.url);
  const since = url.searchParams.get("since");

  const alerts = await getAlerts(auth.teamId, {
    limit: safeInt(url.searchParams.get("limit"), 50, 1, 200),
    since: since || undefined,
  });

  return NextResponse.json({ alerts });
}
