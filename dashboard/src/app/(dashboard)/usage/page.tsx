import { getSessionOrRedirect, getTeamForUser } from "@/lib/auth";
import { getUsageStats } from "@/lib/queries";
import { PLANS } from "@/lib/plans";
import type { PlanName } from "@/lib/plans";

export default async function UsagePage() {
  const user = await getSessionOrRedirect();
  const team = await getTeamForUser(user.id);
  const usage = await getUsageStats(team.id);
  const plan = PLANS[team.plan as PlanName] ?? PLANS.free;
  const pct = Math.min((usage.eventCount / plan.max_events) * 100, 100);

  return (
    <div className="max-w-2xl space-y-6">
      <h1 className="text-2xl font-semibold tracking-tight">Usage</h1>

      <div className="rounded-md border p-6 space-y-4">
        <div className="flex items-end justify-between">
          <div>
            <div className="text-sm text-muted-foreground">
              Events this month ({usage.currentMonth})
            </div>
            <div className="text-3xl font-semibold">
              {usage.eventCount.toLocaleString()}
            </div>
          </div>
          <div className="text-right text-sm text-muted-foreground">
            {plan.max_events.toLocaleString()} limit ({plan.label} plan)
          </div>
        </div>

        <div className="h-3 rounded-full bg-muted overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${
              pct > 90 ? "bg-red-400" : pct > 70 ? "bg-yellow-400" : "bg-green-400"
            }`}
            style={{ width: `${pct}%` }}
          />
        </div>

        <div className="text-xs text-muted-foreground">
          {pct.toFixed(1)}% of monthly limit used
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div className="rounded-md border p-4 text-center">
          <div className="text-xs text-muted-foreground">Plan</div>
          <div className="mt-1 text-lg font-semibold">{plan.label}</div>
        </div>
        <div className="rounded-md border p-4 text-center">
          <div className="text-xs text-muted-foreground">Retention</div>
          <div className="mt-1 text-lg font-semibold">
            {plan.retention_days}d
          </div>
        </div>
        <div className="rounded-md border p-4 text-center">
          <div className="text-xs text-muted-foreground">API Keys</div>
          <div className="mt-1 text-lg font-semibold">{plan.max_keys}</div>
        </div>
      </div>

      {team.plan === "free" && (
        <div className="rounded-md border border-green-500/30 bg-green-500/5 p-4">
          <div className="font-medium">Need more?</div>
          <p className="mt-1 text-sm text-muted-foreground">
            Upgrade to Pro for 500K events/month, 30-day retention, and 5 API
            keys — $39/mo.
          </p>
        </div>
      )}
    </div>
  );
}
