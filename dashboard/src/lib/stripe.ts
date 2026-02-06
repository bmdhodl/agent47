import Stripe from "stripe";

let _stripe: Stripe | null = null;

export function getStripe(): Stripe {
  if (!_stripe) {
    if (!process.env.STRIPE_SECRET_KEY) {
      throw new Error("STRIPE_SECRET_KEY not set");
    }
    _stripe = new Stripe(process.env.STRIPE_SECRET_KEY);
  }
  return _stripe;
}

export const STRIPE_PLANS: Record<string, string> = {
  pro: process.env.STRIPE_PRICE_PRO ?? "",
  team: process.env.STRIPE_PRICE_TEAM ?? "",
};

export function planFromPriceId(priceId: string): string {
  for (const [plan, id] of Object.entries(STRIPE_PLANS)) {
    if (id === priceId) return plan;
  }
  return "free";
}
