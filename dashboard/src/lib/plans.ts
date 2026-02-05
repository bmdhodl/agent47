export const PLANS = {
  free: {
    label: "Free",
    price: 0,
    retention_days: 7,
    max_events: 10_000,
    max_users: 1,
    max_keys: 2,
  },
  pro: {
    label: "Pro",
    price: 39,
    retention_days: 30,
    max_events: 500_000,
    max_users: 1,
    max_keys: 5,
  },
  team: {
    label: "Team",
    price: 149,
    retention_days: 90,
    max_events: 5_000_000,
    max_users: 10,
    max_keys: 20,
  },
} as const;

export type PlanName = keyof typeof PLANS;
