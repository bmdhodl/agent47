import { z } from "zod";

export const eventSchema = z.object({
  service: z.string().min(1).max(256),
  kind: z.enum(["span", "event"]),
  phase: z.enum(["start", "end", "emit"]),
  trace_id: z.string().min(1).max(64),
  span_id: z.string().min(1).max(64),
  parent_id: z.string().max(64).nullable(),
  name: z.string().min(1).max(512),
  ts: z.number(),
  duration_ms: z.number().nullable(),
  data: z.record(z.string(), z.unknown()).default({}),
  error: z
    .object({
      type: z.string(),
      message: z.string(),
    })
    .nullable(),
  cost_usd: z.number().nullable().optional(),
});

export type IngestEvent = z.infer<typeof eventSchema>;
