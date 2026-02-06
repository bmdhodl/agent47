import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { getStripe, STRIPE_PLANS } from "@/lib/stripe";
import { getSupabaseAdmin } from "@/lib/supabase/admin";

export async function POST(request: Request) {
  const supabase = createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { plan } = await request.json();
  const priceId = STRIPE_PLANS[plan];

  if (!priceId) {
    return NextResponse.json({ error: "Invalid plan" }, { status: 400 });
  }

  const admin = getSupabaseAdmin();
  const { data: team } = await admin
    .from("teams")
    .select("id, stripe_customer_id")
    .eq("owner_id", user.id)
    .single();

  if (!team) {
    return NextResponse.json({ error: "Team not found" }, { status: 404 });
  }

  const stripe = getStripe();

  // Create or reuse Stripe customer
  let customerId = team.stripe_customer_id;
  if (!customerId) {
    const customer = await stripe.customers.create({
      email: user.email,
      metadata: { team_id: team.id },
    });
    customerId = customer.id;
    await admin
      .from("teams")
      .update({ stripe_customer_id: customerId })
      .eq("id", team.id);
  }

  const session = await stripe.checkout.sessions.create({
    customer: customerId,
    mode: "subscription",
    line_items: [{ price: priceId, quantity: 1 }],
    success_url: `${request.headers.get("origin")}/settings?upgraded=true`,
    cancel_url: `${request.headers.get("origin")}/settings`,
    metadata: { team_id: team.id },
  });

  return NextResponse.json({ url: session.url });
}
