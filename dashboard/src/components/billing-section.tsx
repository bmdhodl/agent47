"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";

export function BillingSection({
  currentPlan,
  hasStripeCustomer,
}: {
  currentPlan: string;
  hasStripeCustomer: boolean;
}) {
  const [loading, setLoading] = useState<string | null>(null);
  const { toast } = useToast();

  async function handleUpgrade(plan: string) {
    setLoading(plan);
    try {
      const res = await fetch("/api/billing/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plan }),
      });

      if (!res.ok) {
        const data = await res
          .json()
          .catch(() => ({ error: "Billing service unavailable" }));
        toast({
          title: "Error",
          description: data.error,
          variant: "destructive",
        });
        setLoading(null);
        return;
      }

      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;
      } else {
        toast({
          title: "Error",
          description: "No checkout URL returned",
          variant: "destructive",
        });
      }
    } catch {
      toast({
        title: "Error",
        description: "Could not reach billing service",
        variant: "destructive",
      });
    }
    setLoading(null);
  }

  async function handleManage() {
    setLoading("portal");
    try {
      const res = await fetch("/api/billing/portal", { method: "POST" });

      if (!res.ok) {
        const data = await res
          .json()
          .catch(() => ({ error: "Billing service unavailable" }));
        toast({
          title: "Error",
          description: data.error,
          variant: "destructive",
        });
        setLoading(null);
        return;
      }

      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;
      } else {
        toast({
          title: "Error",
          description: "No portal URL returned",
          variant: "destructive",
        });
      }
    } catch {
      toast({
        title: "Error",
        description: "Could not reach billing service",
        variant: "destructive",
      });
    }
    setLoading(null);
  }

  const plans = [
    {
      name: "pro",
      label: "Pro",
      price: "$39/mo",
      features: ["500K events/month", "30-day retention", "5 API keys"],
    },
    {
      name: "team",
      label: "Team",
      price: "$149/mo",
      features: [
        "5M events/month",
        "90-day retention",
        "20 API keys, 10 users",
      ],
    },
  ];

  return (
    <section className="space-y-4">
      <h2 className="text-lg font-medium">Billing</h2>

      <div className="grid gap-3 sm:grid-cols-2">
        {plans.map((plan) => {
          const isCurrent = currentPlan === plan.name;
          return (
            <div
              key={plan.name}
              className={`rounded-xl border bg-card p-5 space-y-3 transition-colors ${
                isCurrent ? "border-emerald-500/50 bg-emerald-500/5" : ""
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="font-medium">
                  {plan.label}{" "}
                  <span className="text-muted-foreground">{plan.price}</span>
                </div>
                {isCurrent && (
                  <Badge
                    variant="secondary"
                    className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20"
                  >
                    Current
                  </Badge>
                )}
              </div>
              <ul className="text-sm text-muted-foreground space-y-1">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-center gap-2">
                    <span className="h-1 w-1 rounded-full bg-muted-foreground/50" />
                    {f}
                  </li>
                ))}
              </ul>
              {!isCurrent && (
                <Button
                  size="sm"
                  onClick={() => handleUpgrade(plan.name)}
                  disabled={loading !== null}
                  className="w-full"
                >
                  {loading === plan.name ? "Loading..." : "Upgrade"}
                </Button>
              )}
            </div>
          );
        })}
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
    </section>
  );
}
