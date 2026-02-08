import { NextResponse } from "next/server";
import { authenticateApiKey, isAuthSuccess } from "@/lib/api-auth";
import { getAlerts } from "@/lib/queries";

export async function GET(request: Request) {
  const auth = await authenticateApiKey(request);
  if (!isAuthSuccess(auth)) return auth;

  const url = new URL(request.url);
  const limit = url.searchParams.get("limit");
  const since = url.searchParams.get("since");

  const alerts = await getAlerts(auth.teamId, {
    limit: limit ? parseInt(limit, 10) : undefined,
    since: since || undefined,
  });

  return NextResponse.json({ alerts });
}
