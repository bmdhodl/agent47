import Link from "next/link";
import { getSessionOrRedirect, getTeamForUser } from "@/lib/auth";
import { getTraceEvents } from "@/lib/queries";
import { TraceGantt } from "@/components/trace-gantt";
import { ShareButton } from "@/components/share-button";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft } from "lucide-react";

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
      <div className="space-y-6">
        <Link
          href="/traces"
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to traces
        </Link>
        <div className="rounded-xl border bg-card p-12 text-center text-muted-foreground">
          Trace not found
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link
          href="/traces"
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </Link>
        <div className="h-4 w-px bg-border" />
        <h1 className="font-mono text-lg font-semibold">
          {params.traceId.slice(0, 8)}...
        </h1>
        {events[0]?.api_key_name && (
          <Badge variant="secondary" className="text-xs">
            {events[0].api_key_name}
          </Badge>
        )}
        <div className="flex-1" />
        <ShareButton traceId={params.traceId} />
      </div>
      <TraceGantt events={events} />
    </div>
  );
}
