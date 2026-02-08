import { NextResponse } from "next/server";
import { authenticateApiKey, isAuthSuccess } from "@/lib/api-auth";
import { getMonthlyCost, getCostByModel, getSavingsStats } from "@/lib/queries";

export async function GET(request: Request) {
  const auth = await authenticateApiKey(request);
  if (!isAuthSuccess(auth)) return auth;

  const [monthly, byModel, savings] = await Promise.all([
    getMonthlyCost(auth.teamId),
    getCostByModel(auth.teamId),
    getSavingsStats(auth.teamId),
  ]);

  return NextResponse.json({
    monthly: {
      total_cost: monthly.total_cost,
      trace_count: monthly.trace_count,
    },
    by_model: byModel,
    savings: {
      guard_events: savings.guard_events,
      estimated_savings: savings.estimated_savings,
    },
  });
}
