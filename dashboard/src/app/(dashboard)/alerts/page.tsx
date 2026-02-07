import Link from "next/link";
import { getSessionOrRedirect, getTeamForUser } from "@/lib/auth";
import { getAlerts } from "@/lib/queries";
import { Badge } from "@/components/ui/badge";
import { Bell } from "lucide-react";

export default async function AlertsPage() {
  const user = await getSessionOrRedirect();
  const team = await getTeamForUser(user.id);
  const alerts = await getAlerts(team.id);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Alerts</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Guard events and errors from your agents.
        </p>
      </div>

      {alerts.length === 0 ? (
        <div className="rounded-xl border bg-card p-8 sm:p-12">
          <div className="mx-auto max-w-md text-center">
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-muted">
              <Bell className="h-6 w-6 text-muted-foreground" />
            </div>
            <p className="font-medium">No alerts yet</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Guard events and errors will appear here when your agents trigger
              them.
            </p>
            <div className="mx-auto mt-6 max-w-sm rounded-lg bg-muted/50 p-4 text-left overflow-x-auto">
              <p className="mb-2 text-xs font-medium text-muted-foreground">
                Enable guards in your agent:
              </p>
              <pre className="text-xs leading-relaxed whitespace-pre-wrap break-all sm:whitespace-pre sm:break-normal">{`from agentguard47 import Tracer, LoopGuard, BudgetGuard

tracer = Tracer()
loop = LoopGuard(max_repeats=3)
budget = BudgetGuard(max_calls=50)`}</pre>
            </div>
          </div>
        </div>
      ) : (
        <div className="rounded-xl border bg-card divide-y">
          {alerts.map((alert) => {
            const data = (alert.data || {}) as Record<string, unknown>;
            return (
              <Link
                key={alert.id}
                href={`/traces/${alert.trace_id}`}
                className="group flex items-start gap-3 px-4 py-3.5 transition-colors hover:bg-accent/50 sm:items-center sm:gap-4 sm:px-5"
              >
                <div
                  className={`mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full ring-2 ring-offset-2 ring-offset-card sm:mt-0 ${
                    alert.error
                      ? "bg-red-500 ring-red-500/20"
                      : "bg-yellow-500 ring-yellow-500/20"
                  }`}
                />
                <div className="flex-1 min-w-0">
                  <div className="font-mono text-sm font-medium truncate">
                    {alert.name}
                  </div>
                  {alert.name === "guard.budget_exceeded" && (
                    <div className="mt-0.5 text-xs text-yellow-400 truncate">
                      Used {String(data.tokens_used ?? "?")}/
                      {String(data.tokens_limit ?? "?")} tokens,{" "}
                      {String(data.calls_used ?? "?")}/
                      {String(data.calls_limit ?? "?")} calls
                    </div>
                  )}
                  {alert.name === "guard.loop_detected" && (
                    <div className="mt-0.5 text-xs text-yellow-400 truncate">
                      Tool{" "}
                      <code className="rounded bg-muted px-1 py-0.5">
                        {String(data.tool_name ?? "unknown")}
                      </code>{" "}
                      called {String(data.repeat_count ?? "?")} times
                    </div>
                  )}
                  {alert.error && (
                    <div className="mt-0.5 text-xs text-red-400 truncate">
                      {alert.error.type}: {alert.error.message}
                    </div>
                  )}
                  <div className="mt-1.5 flex flex-wrap items-center gap-1.5 sm:hidden">
                    <Badge variant="secondary" className="text-[10px]">
                      {alert.service}
                    </Badge>
                    <span className="text-[10px] text-muted-foreground">
                      {new Date(alert.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                <Badge
                  variant="secondary"
                  className="hidden shrink-0 text-xs sm:inline-flex"
                >
                  {alert.service}
                </Badge>
                {alert.api_key_name && (
                  <Badge
                    variant="outline"
                    className="hidden shrink-0 text-xs sm:inline-flex"
                  >
                    {alert.api_key_name}
                  </Badge>
                )}
                <div className="hidden shrink-0 text-xs text-muted-foreground sm:block">
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
