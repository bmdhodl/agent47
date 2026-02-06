import { NextResponse } from "next/server";
import sql from "@/lib/db";
import { PLANS } from "@/lib/plans";
import type { PlanName } from "@/lib/plans";

export async function GET(request: Request) {
  const authHeader = request.headers.get("authorization");
  if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const teams = await sql`SELECT id, plan FROM teams`;

  if (teams.length === 0) {
    return NextResponse.json({ message: "No teams", deleted: 0 });
  }

  let totalDeleted = 0;

  for (const team of teams) {
    const plan = PLANS[team.plan as PlanName] ?? PLANS.free;
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - plan.retention_days);

    const result = await sql`
      DELETE FROM events
      WHERE team_id = ${team.id} AND created_at < ${cutoff.toISOString()}
    `;

    totalDeleted += result.count;
  }

  return NextResponse.json({
    message: "Retention cleanup complete",
    deleted: totalDeleted,
    teams: teams.length,
  });
}
