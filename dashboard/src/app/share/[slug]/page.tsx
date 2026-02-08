import type { Metadata } from "next";
import sql from "@/lib/db";
import { getTraceEvents } from "@/lib/queries";
import { TraceGantt } from "@/components/trace-gantt";

interface Props {
  params: { slug: string };
}

async function getSharedTrace(slug: string) {
  const rows = await sql`
    SELECT team_id, trace_id, expires_at FROM shared_traces
    WHERE slug = ${slug}
  `;

  if (rows.length === 0) return null;

  const row = rows[0];
  if (row.expires_at && new Date(row.expires_at as string) < new Date()) {
    return null;
  }

  return { teamId: row.team_id as string, traceId: row.trace_id as string };
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const shared = await getSharedTrace(params.slug);
  if (!shared) {
    return { title: "Trace not found — AgentGuard" };
  }

  return {
    title: `Trace ${shared.traceId.slice(0, 8)}... — AgentGuard`,
    description: "Shared agent trace — view spans, tool calls, LLM calls, guard triggers, and costs.",
    openGraph: {
      title: `Agent Trace ${shared.traceId.slice(0, 8)}...`,
      description: "Shared agent trace on AgentGuard — observability for multi-agent AI systems.",
      type: "website",
    },
  };
}

export default async function SharedTracePage({ params }: Props) {
  const shared = await getSharedTrace(params.slug);

  if (!shared) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="mx-auto max-w-md space-y-4 text-center">
          <h1 className="text-2xl font-semibold">Trace not found</h1>
          <p className="text-muted-foreground">
            This shared trace link has expired or doesn&apos;t exist.
          </p>
          <a
            href="https://agentguard.dev"
            className="inline-block rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Learn about AgentGuard
          </a>
        </div>
      </div>
    );
  }

  const events = await getTraceEvents(shared.teamId, shared.traceId);

  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div className="space-y-1">
            <h1 className="font-mono text-lg font-semibold">
              Trace {shared.traceId.slice(0, 8)}...
            </h1>
            <p className="text-xs text-muted-foreground">
              Shared trace — read only
            </p>
          </div>
          <a
            href="https://agentguard.dev"
            className="inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
          >
            Powered by AgentGuard
          </a>
        </div>

        {events.length === 0 ? (
          <div className="rounded-xl border bg-card p-12 text-center text-muted-foreground">
            Trace data has been deleted (retention policy)
          </div>
        ) : (
          <TraceGantt events={events} />
        )}

        {/* CTA */}
        <div className="mt-12 rounded-xl border bg-card p-6 text-center">
          <h2 className="text-lg font-semibold">
            Monitor your AI agents with AgentGuard
          </h2>
          <p className="mx-auto mt-2 max-w-md text-sm text-muted-foreground">
            Trace reasoning, detect loops, enforce budgets, and replay runs.
            Open-source SDK, hosted dashboard.
          </p>
          <div className="mt-4 flex items-center justify-center gap-3">
            <a
              href="https://agentguard.dev"
              className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
            >
              Get started free
            </a>
            <a
              href="https://github.com/bmdhodl/agent47"
              className="rounded-lg border px-4 py-2 text-sm font-medium transition-colors hover:bg-accent"
            >
              View on GitHub
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
