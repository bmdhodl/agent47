import { NextResponse } from "next/server";
import { authenticateApiKey, isAuthSuccess } from "@/lib/api-auth";
import { getUsageStats } from "@/lib/queries";
import { PLANS } from "@/lib/plans";
import type { PlanName } from "@/lib/plans";
import sql from "@/lib/db";

export async function GET(request: Request) {
  const auth = await authenticateApiKey(request);
  if (!isAuthSuccess(auth)) return auth;

  const usage = await getUsageStats(auth.teamId);

  const teamRows = await sql`
    SELECT plan FROM teams WHERE id = ${auth.teamId}
  `;
  const planName = (teamRows[0]?.plan as PlanName) ?? "free";
  const plan = PLANS[planName] ?? PLANS.free;

  return NextResponse.json({
    plan: planName,
    current_month: usage.currentMonth,
    event_count: usage.eventCount,
    event_limit: plan.max_events,
    retention_days: plan.retention_days,
    max_keys: plan.max_keys,
    max_users: plan.max_users,
  });
}
