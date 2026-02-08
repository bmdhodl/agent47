import { NextResponse } from "next/server";
import { authenticateApiKey, isAuthSuccess } from "@/lib/api-auth";
import { getTraceEvents } from "@/lib/queries";

export async function GET(
  request: Request,
  { params }: { params: { traceId: string } },
) {
  const auth = await authenticateApiKey(request);
  if (!isAuthSuccess(auth)) return auth;

  const events = await getTraceEvents(auth.teamId, params.traceId);

  if (events.length === 0) {
    return NextResponse.json({ error: "Trace not found" }, { status: 404 });
  }

  return NextResponse.json({ trace_id: params.traceId, events });
}
