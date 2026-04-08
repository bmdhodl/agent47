import test from "node:test";
import assert from "node:assert/strict";

import { buildToolShape } from "../schema.js";

test("buildToolShape supports string, number, and boolean fields", () => {
  const shape = buildToolShape(
    {
      trace_id: { type: "string", description: "trace" },
      limit: { type: "number", description: "limit" },
      include_errors: { type: "boolean", description: "flag" },
    },
    ["trace_id", "include_errors"],
  );

  assert.equal(shape.trace_id.safeParse("trace_1").success, true);
  assert.equal(shape.limit.safeParse(5).success, true);
  assert.equal(shape.include_errors.safeParse(true).success, true);
  assert.equal(shape.limit.safeParse(undefined).success, true);
  assert.equal(shape.include_errors.safeParse("yes").success, false);
});
