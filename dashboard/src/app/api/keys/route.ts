import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/next-auth";
import sql from "@/lib/db";
import { generateApiKey } from "@/lib/api-key";
import { PLANS } from "@/lib/plans";
import type { PlanName } from "@/lib/plans";

export async function POST(request: Request) {
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const userId = (session.user as { id: string }).id;
  const { name, team_id } = await request.json();

  // Verify user owns the team
  const teams = await sql`
    SELECT id, plan FROM teams
    WHERE id = ${team_id} AND owner_id = ${userId}
  `;

  if (teams.length === 0) {
    return NextResponse.json({ error: "Team not found" }, { status: 404 });
  }

  const team = teams[0];
  const plan = PLANS[team.plan as PlanName] ?? PLANS.free;

  // Check key limit
  const countResult = await sql`
    SELECT COUNT(*)::int as count FROM api_keys
    WHERE team_id = ${team_id} AND revoked_at IS NULL
  `;

  if (countResult[0].count >= plan.max_keys) {
    return NextResponse.json(
      { error: "Key limit reached. Upgrade your plan." },
      { status: 403 },
    );
  }

  const { raw, hash, prefix } = generateApiKey();

  await sql`
    INSERT INTO api_keys (team_id, key_hash, prefix, name)
    VALUES (${team_id}, ${hash}, ${prefix}, ${name || "Default"})
  `;

  return NextResponse.json({ raw_key: raw, prefix });
}
