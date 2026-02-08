# Pricing

## SDK
- Free (MIT, zero dependencies, always free)

## Hosted Dashboard (live)

| | Free | Pro | Team |
|---|---|---|---|
| **Price** | $0 | $39/month | $149/month |
| **Events/month** | 10,000 | 500,000 | 5,000,000 |
| **Data retention** | 7 days | 30 days | 90 days |
| **API keys** | 2 | 5 | 20 |
| **Users** | 1 | 1 | 10 |

## What's included (all plans)
- Trace ingestion via HttpSink
- Trace list and Gantt visualization
- Cost tracking (by model, by key)
- Guard alerts view
- Usage monitoring
- Read API (v1) access
- MCP server access
- Public trace sharing

## Pricing principle
Price for risk reduction and saved engineering time, not per-token usage. The free tier is generous enough to prove value; upgrades are driven by volume and retention needs.

## Billing implementation
- Stripe Checkout for upgrades
- Stripe Customer Portal for management
- Webhooks for subscription lifecycle
- Usage enforced at ingest time (quota check before insert)
