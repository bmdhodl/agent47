import Link from "next/link";
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
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Usage</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Monitor your event consumption and plan limits.
        </p>
      </div>

      <div className="rounded-xl border bg-card p-5 space-y-5 sm:p-6">
        <div className="flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <div className="text-sm text-muted-foreground">
              Events this month ({usage.currentMonth})
            </div>
            <div className="text-3xl font-semibold tabular-nums sm:text-4xl">
              {usage.eventCount.toLocaleString()}
            </div>
          </div>
          <div className="text-sm text-muted-foreground sm:text-right">
            {plan.max_events.toLocaleString()} limit
            <span className="font-medium text-foreground"> ({plan.label})</span>
          </div>
        </div>

        <div className="space-y-2">
          <div className="h-3 rounded-full bg-muted overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${
                pct > 90
                  ? "bg-red-500"
                  : pct > 70
                    ? "bg-yellow-500"
                    : "bg-emerald-500"
              }`}
              style={{ width: `${pct}%` }}
            />
          </div>
          <div className="text-xs text-muted-foreground tabular-nums">
            {pct.toFixed(1)}% of monthly limit used
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3">
        {[
          { label: "Plan", value: plan.label },
          { label: "Retention", value: `${plan.retention_days}d` },
          { label: "API Keys", value: String(plan.max_keys) },
        ].map((stat) => (
          <div
            key={stat.label}
            className="rounded-xl border bg-card p-4 text-center"
          >
            <div className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground/70">
              {stat.label}
            </div>
            <div className="mt-1 text-xl font-semibold">{stat.value}</div>
          </div>
        ))}
      </div>

      {team.plan === "free" && (
        <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-5">
          <div className="font-medium">Need more capacity?</div>
          <p className="mt-1 text-sm text-muted-foreground">
            Upgrade to Pro for 500K events/month, 30-day retention, and 5 API
            keys.{" "}
            <Link
              href="/settings"
              className="font-medium text-foreground underline underline-offset-4 hover:no-underline"
            >
              View plans
            </Link>
          </p>
        </div>
      )}
    </div>
  );
}
