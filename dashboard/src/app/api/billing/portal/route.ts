import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { getStripe } from "@/lib/stripe";
import { getSupabaseAdmin } from "@/lib/supabase/admin";

export async function POST(request: Request) {
  const supabase = createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const admin = getSupabaseAdmin();
  const { data: team } = await admin
    .from("teams")
    .select("stripe_customer_id")
    .eq("owner_id", user.id)
    .single();

  if (!team?.stripe_customer_id) {
    return NextResponse.json(
      { error: "No billing account" },
      { status: 400 },
    );
  }

  const stripe = getStripe();
  const session = await stripe.billingPortal.sessions.create({
    customer: team.stripe_customer_id,
    return_url: `${request.headers.get("origin")}/settings`,
  });

  return NextResponse.json({ url: session.url });
}
