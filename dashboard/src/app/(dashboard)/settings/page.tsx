import { getSessionOrRedirect, getTeamForUser } from "@/lib/auth";
import sql from "@/lib/db";
import { PLANS } from "@/lib/plans";
import type { PlanName } from "@/lib/plans";
import { ApiKeyManager } from "@/components/api-key-manager";
import { BillingSection } from "@/components/billing-section";
import { Separator } from "@/components/ui/separator";

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
        <p className="mt-1 text-muted-foreground">
          Manage your API keys and account.
        </p>
      </div>

      <div className="space-y-2">
        <h2 className="text-lg font-medium">Account</h2>
        <div className="rounded-md border p-4 text-sm space-y-1">
          <p>
            <span className="text-muted-foreground">Email:</span> {user.email}
          </p>
          <p>
            <span className="text-muted-foreground">Plan:</span> {plan.label}
          </p>
          <p>
            <span className="text-muted-foreground">Team:</span> {team.name}
          </p>
        </div>
      </div>

      <Separator />

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

      <Separator />

      <BillingSection
        currentPlan={team.plan}
        hasStripeCustomer={!!team.stripe_customer_id}
      />
    </div>
  );
}
