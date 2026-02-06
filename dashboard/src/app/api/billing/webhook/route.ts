import { NextResponse } from "next/server";
import { getStripe, planFromPriceId } from "@/lib/stripe";
import sql from "@/lib/db";

export async function POST(request: Request) {
  const body = await request.text();
  const sig = request.headers.get("stripe-signature");

  if (!sig) {
    return NextResponse.json({ error: "Missing signature" }, { status: 400 });
  }

  const stripe = getStripe();
  let event;

  try {
    event = stripe.webhooks.constructEvent(
      body,
      sig,
      process.env.STRIPE_WEBHOOK_SECRET!,
    );
  } catch {
    return NextResponse.json({ error: "Invalid signature" }, { status: 400 });
  }

  switch (event.type) {
    case "checkout.session.completed": {
      const session = event.data.object;
      const teamId = session.metadata?.team_id;
      if (!teamId) break;

      if (session.subscription) {
        const sub = await stripe.subscriptions.retrieve(
          session.subscription as string,
        );
        const priceId = sub.items.data[0]?.price.id;
        const plan = priceId ? planFromPriceId(priceId) : "pro";

        await sql`
          UPDATE teams SET
            plan = ${plan},
            stripe_subscription_id = ${sub.id},
            stripe_customer_id = ${session.customer as string}
          WHERE id = ${teamId}
        `;
      }
      break;
    }

    case "customer.subscription.updated": {
      const sub = event.data.object;
      const priceId = sub.items.data[0]?.price.id;
      const plan = priceId ? planFromPriceId(priceId) : "free";

      await sql`
        UPDATE teams SET plan = ${plan}
        WHERE stripe_subscription_id = ${sub.id}
      `;
      break;
    }

    case "customer.subscription.deleted": {
      const sub = event.data.object;
      await sql`
        UPDATE teams SET plan = 'free', stripe_subscription_id = NULL
        WHERE stripe_subscription_id = ${sub.id}
      `;
      break;
    }
  }

  return NextResponse.json({ received: true });
}
