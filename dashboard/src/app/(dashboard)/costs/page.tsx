import Link from "next/link";
import { getSessionOrRedirect, getTeamForUser } from "@/lib/auth";
import {
  getMonthlyCost,
  getSavingsStats,
  getCostByModel,
  getCostByKey,
  getExpensiveTraces,
} from "@/lib/queries";

function formatCost(usd: number): string {
  if (usd === 0) return "$0.00";
  if (usd < 0.01) return `$${usd.toFixed(4)}`;
  return `$${usd.toFixed(2)}`;
}

export default async function CostsPage() {
  const user = await getSessionOrRedirect();
  const team = await getTeamForUser(user.id);

  const [monthly, savings, byModel, byKey, expensive] = await Promise.all([
    getMonthlyCost(team.id),
    getSavingsStats(team.id),
    getCostByModel(team.id),
    getCostByKey(team.id),
    getExpensiveTraces(team.id),
  ]);

  const showSavings = savings.guard_events > 0;

  return (
    <div className="max-w-4xl space-y-6">
      <h1 className="text-2xl font-semibold tracking-tight">Costs</h1>

      {/* Savings banner */}
      {showSavings && (
        <div className="rounded-md border border-green-500/30 bg-green-500/5 p-4 sm:p-5">
          <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <div className="text-sm font-medium text-green-700 dark:text-green-400">
                Guards prevented {savings.guard_events} runaway{savings.guard_events !== 1 ? "s" : ""} this month
              </div>
              <div className="text-2xl font-bold text-green-700 dark:text-green-400 sm:text-3xl">
                ~{formatCost(savings.estimated_savings)} saved
              </div>
            </div>
            {team.plan === "free" && (
              <div className="text-sm text-muted-foreground">
                <Link href="/settings" className="underline hover:text-foreground">
                  Upgrade to Pro
                </Link>{" "}
                for detailed cost breakdown
              </div>
            )}
          </div>
        </div>
      )}

      {/* Summary cards */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <div className="rounded-md border p-4 text-center">
          <div className="text-xs text-muted-foreground">Total Cost This Month</div>
          <div className="mt-1 text-2xl font-semibold">{formatCost(monthly.total_cost)}</div>
        </div>
        <div className="rounded-md border p-4 text-center">
          <div className="text-xs text-muted-foreground">Traces This Month</div>
          <div className="mt-1 text-2xl font-semibold">{monthly.trace_count.toLocaleString()}</div>
        </div>
        <div className="rounded-md border p-4 text-center">
          <div className="text-xs text-muted-foreground">Avg Cost per Trace</div>
          <div className="mt-1 text-2xl font-semibold">
            {monthly.trace_count > 0
              ? formatCost(monthly.total_cost / monthly.trace_count)
              : "$0.00"}
          </div>
        </div>
      </div>

      {/* Cost by model */}
      <div className="space-y-2">
        <h2 className="text-lg font-semibold">Cost by Model</h2>
        {byModel.length === 0 ? (
          <div className="rounded-md border p-4 text-center text-sm text-muted-foreground">
            No cost data yet. Cost tracking starts when the SDK sends events with cost_usd.
          </div>
        ) : (
          <div className="rounded-md border">
            <div className="divide-y">
              {byModel.map((row) => (
                <div
                  key={row.model}
                  className="flex items-center justify-between px-4 py-3 text-sm"
                >
                  <div>
                    <span className="font-mono">{row.model}</span>
                    <span className="ml-2 text-xs text-muted-foreground">
                      {row.call_count} call{row.call_count !== 1 ? "s" : ""}
                    </span>
                  </div>
                  <span className="font-semibold">{formatCost(Number(row.total_cost))}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Cost by API key */}
      {byKey.length > 0 && (
        <div className="space-y-2">
          <h2 className="text-lg font-semibold">Cost by API Key</h2>
          <div className="rounded-md border">
            <div className="divide-y">
              {byKey.map((row) => (
                <div
                  key={row.api_key_prefix}
                  className="flex items-center justify-between px-4 py-3 text-sm"
                >
                  <div>
                    <span className="font-medium">{row.api_key_name}</span>
                    <span className="ml-2 text-xs text-muted-foreground font-mono">
                      {row.api_key_prefix}...
                    </span>
                    <span className="ml-2 text-xs text-muted-foreground">
                      {row.trace_count} trace{row.trace_count !== 1 ? "s" : ""}
                    </span>
                  </div>
                  <span className="font-semibold">{formatCost(Number(row.total_cost))}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Most expensive traces */}
      {expensive.length > 0 && (
        <div className="space-y-2">
          <h2 className="text-lg font-semibold">Most Expensive Traces</h2>
          <div className="rounded-md border">
            <div className="divide-y">
              {expensive.map((trace) => (
                <Link
                  key={trace.trace_id}
                  href={`/traces/${trace.trace_id}`}
                  className="flex items-center justify-between px-4 py-3 text-sm transition-colors hover:bg-accent/50"
                >
                  <div className="min-w-0 flex-1">
                    <div className="font-mono text-sm truncate">
                      {trace.root_name || trace.trace_id.slice(0, 8)}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {trace.event_count} events &middot;{" "}
                      {new Date(trace.started_at).toLocaleString()}
                    </div>
                  </div>
                  <span className="ml-3 font-semibold shrink-0">
                    {formatCost(Number(trace.total_cost))}
                  </span>
                </Link>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Empty state */}
      {monthly.total_cost === 0 && !showSavings && (
        <div className="rounded-md border p-6 text-center">
          <h2 className="text-lg font-semibold">No cost data yet</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Cost tracking starts automatically when you use{" "}
            <code className="rounded bg-muted px-1.5 py-0.5 text-xs">agentguard47 &gt;= 0.5.0</code>{" "}
            with <code className="rounded bg-muted px-1.5 py-0.5 text-xs">patch_openai()</code> or{" "}
            <code className="rounded bg-muted px-1.5 py-0.5 text-xs">patch_anthropic()</code>.
          </p>
          <div className="mt-4 rounded-md bg-muted p-3 text-left overflow-x-auto">
            <pre className="text-xs leading-relaxed whitespace-pre">{`from agentguard import Tracer, BudgetGuard
from agentguard.instrument import patch_openai

tracer = Tracer(sink=sink)
patch_openai(tracer)  # auto-tracks cost per call

# Or use BudgetGuard to stop runaway spending:
guard = BudgetGuard(max_cost_usd=5.00)`}</pre>
          </div>
        </div>
      )}
    </div>
  );
}
