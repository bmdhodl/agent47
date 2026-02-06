import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { generateApiKey } from "@/lib/api-key";
import { PLANS } from "@/lib/plans";
import type { PlanName } from "@/lib/plans";

export async function POST(request: Request) {
  const supabase = createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { name, team_id } = await request.json();

  // Verify user owns the team
  const { data: team } = await supabase
    .from("teams")
    .select("id, plan")
    .eq("id", team_id)
    .eq("owner_id", user.id)
    .single();

  if (!team) {
    return NextResponse.json({ error: "Team not found" }, { status: 404 });
  }

  // Check key limit
  const plan = PLANS[team.plan as PlanName] ?? PLANS.free;
  const { count } = await supabase
    .from("api_keys")
    .select("*", { count: "exact", head: true })
    .eq("team_id", team_id)
    .is("revoked_at", null);

  if ((count ?? 0) >= plan.max_keys) {
    return NextResponse.json(
      { error: "Key limit reached. Upgrade your plan." },
      { status: 403 },
    );
  }

  const { raw, hash, prefix } = generateApiKey();

  const { error } = await supabase.from("api_keys").insert({
    team_id,
    key_hash: hash,
    prefix,
    name: name || "Default",
  });

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({ raw_key: raw, prefix });
}
