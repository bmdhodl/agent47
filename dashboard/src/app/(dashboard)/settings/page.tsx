import { getSessionOrRedirect, getTeamForUser } from "@/lib/auth";
import sql from "@/lib/db";
import { PLANS } from "@/lib/plans";
import type { PlanName } from "@/lib/plans";
import { ApiKeyManager } from "@/components/api-key-manager";
import { BillingSection } from "@/components/billing-section";
import { PasswordChangeForm } from "@/components/password-change-form";

export default async function SettingsPage() {
  const user = await getSessionOrRedirect();
  const team = await getTeamForUser(user.id);

  const keys = await sql`
    SELECT id, prefix, name, created_at, revoked_at
    FROM api_keys
    WHERE team_id = ${team.id}
    ORDER BY created_at DESC
  `;

  const plan = PLANS[team.plan as PlanName] ?? PLANS.free;
  const activeKeys = keys.filter((k) => !k.revoked_at);

  return (
    <div className="max-w-2xl space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Manage your API keys, billing, and account.
        </p>
      </div>

      <section className="space-y-3">
        <h2 className="text-lg font-medium">Account</h2>
        <div className="rounded-xl border bg-card p-5 text-sm space-y-2">
          {[
            { label: "Email", value: user.email },
            { label: "Plan", value: plan.label },
            { label: "Team", value: team.name },
          ].map((item) => (
            <div key={item.label} className="flex items-center gap-2">
              <span className="w-16 text-muted-foreground">{item.label}</span>
              <span className="font-medium">{item.value}</span>
            </div>
          ))}
        </div>
      </section>

      <div className="h-px bg-border" />

      <ApiKeyManager
        teamId={team.id}
        keys={keys.map((k) => ({
          id: k.id,
          prefix: k.prefix,
          name: k.name,
          created_at: k.created_at,
          revoked_at: k.revoked_at,
        }))}
        maxKeys={plan.max_keys}
        activeCount={activeKeys.length}
      />

      <div className="h-px bg-border" />

      <BillingSection
        currentPlan={team.plan}
        hasStripeCustomer={!!team.stripe_customer_id}
      />

      <div className="h-px bg-border" />

      <PasswordChangeForm />
    </div>
  );
}
