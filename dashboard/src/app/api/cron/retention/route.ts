import { NextResponse } from "next/server";
import { getSupabaseAdmin } from "@/lib/supabase/admin";
import { PLANS } from "@/lib/plans";
import type { PlanName } from "@/lib/plans";

export async function GET(request: Request) {
  // Verify cron secret (Vercel sets this automatically for cron jobs)
  const authHeader = request.headers.get("authorization");
  if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const admin = getSupabaseAdmin();

  // Get all teams
  const { data: teams } = await admin
    .from("teams")
    .select("id, plan");

  if (!teams || teams.length === 0) {
    return NextResponse.json({ message: "No teams", deleted: 0 });
  }

  let totalDeleted = 0;

  for (const team of teams) {
    const plan = PLANS[team.plan as PlanName] ?? PLANS.free;
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - plan.retention_days);

    const { count } = await admin
      .from("events")
      .delete({ count: "exact" })
      .eq("team_id", team.id)
      .lt("created_at", cutoff.toISOString());

    totalDeleted += count ?? 0;
  }

  return NextResponse.json({
    message: "Retention cleanup complete",
    deleted: totalDeleted,
    teams: teams.length,
  });
}
