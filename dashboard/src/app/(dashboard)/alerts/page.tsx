import Link from "next/link";
import { getSessionOrRedirect, getTeamForUser } from "@/lib/auth";
import { getAlerts } from "@/lib/queries";
import { Badge } from "@/components/ui/badge";

export default async function AlertsPage() {
  const user = await getSessionOrRedirect();
  const team = await getTeamForUser(user.id);
  const alerts = await getAlerts(team.id);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold tracking-tight">Alerts</h1>
      {alerts.length === 0 ? (
        <div className="rounded-md border p-12 text-center">
          <p className="text-muted-foreground">No alerts yet.</p>
          <p className="mt-2 text-sm text-muted-foreground">
            Guard events and errors will appear here when your agents trigger them.
          </p>
          <div className="mx-auto mt-4 max-w-md rounded-md bg-muted p-4 text-left">
            <p className="mb-2 text-xs font-medium text-muted-foreground">Enable guards in your agent:</p>
            <pre className="text-xs leading-relaxed">{`from agentguard47 import Tracer, LoopGuard, BudgetGuard

tracer = Tracer()
loop = LoopGuard(max_repeats=3)
budget = BudgetGuard(max_calls=50)`}</pre>
          </div>
        </div>
      ) : (
        <div className="rounded-md border divide-y">
          {alerts.map((alert) => {
            const data = (alert.data || {}) as Record<string, unknown>;
            return (
              <Link
                key={alert.id}
                href={`/traces/${alert.trace_id}`}
                className="flex items-center gap-4 px-4 py-3 transition-colors hover:bg-accent/50"
              >
                <div
                  className={`h-2 w-2 rounded-full shrink-0 ${
                    alert.error ? "bg-red-400" : "bg-yellow-400"
                  }`}
                />
                <div className="flex-1 min-w-0">
                  <div className="font-mono text-sm">{alert.name}</div>
                  {alert.name === "guard.budget_exceeded" && (
                    <div className="text-xs text-yellow-400">
                      Used {String(data.tokens_used ?? "?")}/{String(data.tokens_limit ?? "?")} tokens, {String(data.calls_used ?? "?")}/{String(data.calls_limit ?? "?")} calls
                    </div>
                  )}
                  {alert.name === "guard.loop_detected" && (
                    <div className="text-xs text-yellow-400">
                      Tool <code className="rounded bg-muted px-1">{String(data.tool_name ?? "unknown")}</code> called {String(data.repeat_count ?? "?")} times in a row
                    </div>
                  )}
                  {alert.error && (
                    <div className="text-xs text-red-400">
                      {alert.error.type}: {alert.error.message}
                    </div>
                  )}
                </div>
                <Badge variant="secondary" className="text-xs">
                  {alert.service}
                </Badge>
                {alert.api_key_name && (
                  <Badge variant="outline" className="text-xs">
                    {alert.api_key_name}
                  </Badge>
                )}
                <div className="text-xs text-muted-foreground shrink-0">
                  {new Date(alert.created_at).toLocaleString()}
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
