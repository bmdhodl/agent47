import Link from "next/link";
import { getSessionOrRedirect, getTeamForUser } from "@/lib/auth";
import { getTraceEvents } from "@/lib/queries";
import { TraceGantt } from "@/components/trace-gantt";

export default async function TraceDetailPage({
  params,
}: {
  params: { traceId: string };
}) {
  const user = await getSessionOrRedirect();
  const team = await getTeamForUser(user.id);
  const events = await getTraceEvents(team.id, params.traceId);

  if (events.length === 0) {
    return (
      <div className="space-y-4">
        <Link
          href="/traces"
          className="text-sm text-muted-foreground hover:text-foreground"
        >
          &larr; Back to traces
        </Link>
        <div className="rounded-md border p-12 text-center text-muted-foreground">
          Trace not found
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <Link
          href="/traces"
          className="text-sm text-muted-foreground hover:text-foreground"
        >
          &larr; Back
        </Link>
        <h1 className="font-mono text-lg font-semibold">
          {params.traceId.slice(0, 8)}...
        </h1>
      </div>
      <TraceGantt events={events} />
    </div>
  );
}
