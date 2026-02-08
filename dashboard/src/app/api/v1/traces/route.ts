import { NextResponse } from "next/server";
import { authenticateApiKey, isAuthSuccess } from "@/lib/api-auth";
import { getTraceList } from "@/lib/queries";

export async function GET(request: Request) {
  const auth = await authenticateApiKey(request);
  if (!isAuthSuccess(auth)) return auth;

  const url = new URL(request.url);
  const limit = url.searchParams.get("limit");
  const offset = url.searchParams.get("offset");
  const service = url.searchParams.get("service");
  const since = url.searchParams.get("since");
  const until = url.searchParams.get("until");

  const traces = await getTraceList(auth.teamId, {
    limit: limit ? parseInt(limit, 10) : undefined,
    offset: offset ? parseInt(offset, 10) : undefined,
    service: service || undefined,
    since: since || undefined,
    until: until || undefined,
  });

  return NextResponse.json({ traces });
}
