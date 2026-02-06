import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/next-auth";
import sql from "@/lib/db";
import { getStripe } from "@/lib/stripe";

export async function POST(request: Request) {
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const userId = (session.user as { id: string }).id;

  const teams = await sql`
    SELECT stripe_customer_id FROM teams
    WHERE owner_id = ${userId}
  `;

  if (teams.length === 0 || !teams[0].stripe_customer_id) {
    return NextResponse.json(
      { error: "No billing account" },
      { status: 400 },
    );
  }

  try {
    const stripe = getStripe();
    const returnUrl = process.env.NEXTAUTH_URL
      ? `${process.env.NEXTAUTH_URL}/settings`
      : `${request.headers.get("origin")}/settings`;

    const portalSession = await stripe.billingPortal.sessions.create({
      customer: teams[0].stripe_customer_id,
      return_url: returnUrl,
    });

    return NextResponse.json({ url: portalSession.url });
  } catch {
    return NextResponse.json(
      { error: "Billing service unavailable" },
      { status: 502 },
    );
  }
}
