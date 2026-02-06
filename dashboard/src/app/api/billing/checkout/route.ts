import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/next-auth";
import sql from "@/lib/db";
import { getStripe, STRIPE_PLANS } from "@/lib/stripe";

function getBaseUrl(request: Request): string {
  const origin = request.headers.get("origin");
  const allowed = process.env.NEXTAUTH_URL;
  if (allowed && origin && new URL(origin).origin === new URL(allowed).origin) {
    return origin;
  }
  return allowed || origin || "";
}

export async function POST(request: Request) {
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const userId = (session.user as { id: string }).id;
  const { plan } = await request.json();
  const priceId = STRIPE_PLANS[plan];

  if (!priceId) {
    return NextResponse.json({ error: "Invalid plan" }, { status: 400 });
  }

  const teams = await sql`
    SELECT id, stripe_customer_id FROM teams
    WHERE owner_id = ${userId}
  `;

  if (teams.length === 0) {
    return NextResponse.json({ error: "Team not found" }, { status: 404 });
  }

  const team = teams[0];

  try {
    const stripe = getStripe();

    let customerId = team.stripe_customer_id;
    if (!customerId) {
      const customer = await stripe.customers.create({
        email: session.user.email!,
        metadata: { team_id: team.id },
      });
      customerId = customer.id;
      await sql`
        UPDATE teams SET stripe_customer_id = ${customerId}
        WHERE id = ${team.id}
      `;
    }

    const baseUrl = getBaseUrl(request);
    const checkoutSession = await stripe.checkout.sessions.create({
      customer: customerId,
      mode: "subscription",
      line_items: [{ price: priceId, quantity: 1 }],
      success_url: `${baseUrl}/settings?upgraded=true`,
      cancel_url: `${baseUrl}/settings`,
      metadata: { team_id: team.id },
    });

    return NextResponse.json({ url: checkoutSession.url });
  } catch {
    return NextResponse.json(
      { error: "Billing service unavailable" },
      { status: 502 },
    );
  }
}
