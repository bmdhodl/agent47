"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";

export function BillingSection({
  currentPlan,
  hasStripeCustomer,
}: {
  currentPlan: string;
  hasStripeCustomer: boolean;
}) {
  const [loading, setLoading] = useState<string | null>(null);

  async function handleUpgrade(plan: string) {
    setLoading(plan);
    const res = await fetch("/api/billing/checkout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ plan }),
    });

    const data = await res.json();
    if (data.url) {
      window.location.href = data.url;
    }
    setLoading(null);
  }

  async function handleManage() {
    setLoading("portal");
    const res = await fetch("/api/billing/portal", { method: "POST" });
    const data = await res.json();
    if (data.url) {
      window.location.href = data.url;
    }
    setLoading(null);
  }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-medium">Billing</h2>

      <div className="grid gap-3 sm:grid-cols-2">
        <div
          className={`rounded-md border p-4 space-y-2 ${
            currentPlan === "pro" ? "border-green-500/50" : ""
          }`}
        >
          <div className="font-medium">Pro — $39/mo</div>
          <ul className="text-sm text-muted-foreground space-y-1">
            <li>500K events/month</li>
            <li>30-day retention</li>
            <li>5 API keys</li>
          </ul>
          {currentPlan === "pro" ? (
            <div className="text-sm text-green-400">Current plan</div>
          ) : (
            <Button
              size="sm"
              onClick={() => handleUpgrade("pro")}
              disabled={loading !== null}
            >
              {loading === "pro" ? "Loading..." : "Upgrade"}
            </Button>
          )}
        </div>

        <div
          className={`rounded-md border p-4 space-y-2 ${
            currentPlan === "team" ? "border-green-500/50" : ""
          }`}
        >
          <div className="font-medium">Team — $149/mo</div>
          <ul className="text-sm text-muted-foreground space-y-1">
            <li>5M events/month</li>
            <li>90-day retention</li>
            <li>20 API keys, 10 users</li>
          </ul>
          {currentPlan === "team" ? (
            <div className="text-sm text-green-400">Current plan</div>
          ) : (
            <Button
              size="sm"
              onClick={() => handleUpgrade("team")}
              disabled={loading !== null}
            >
              {loading === "team" ? "Loading..." : "Upgrade"}
            </Button>
          )}
        </div>
      </div>

      {hasStripeCustomer && (
        <Button
          variant="outline"
          size="sm"
          onClick={handleManage}
          disabled={loading !== null}
        >
          {loading === "portal" ? "Loading..." : "Manage billing"}
        </Button>
      )}
    </div>
  );
}
