import test from "node:test";
import assert from "node:assert/strict";

import { AgentGuardClient } from "../client.js";

test("client requires AGENTGUARD_API_KEY", () => {
  const previousKey = process.env.AGENTGUARD_API_KEY;
  delete process.env.AGENTGUARD_API_KEY;
  try {
    assert.throws(() => new AgentGuardClient(), /AGENTGUARD_API_KEY/);
  } finally {
    if (previousKey === undefined) {
      delete process.env.AGENTGUARD_API_KEY;
    } else {
      process.env.AGENTGUARD_API_KEY = previousKey;
    }
  }
});

test("client trims base URL, encodes trace IDs, and sends bearer auth", async () => {
  const previousKey = process.env.AGENTGUARD_API_KEY;
  const previousUrl = process.env.AGENTGUARD_URL;
  const previousFetch = globalThis.fetch;
  let requestedUrl = "";
  let authorization = "";

  process.env.AGENTGUARD_API_KEY = "ag_test";
  process.env.AGENTGUARD_URL = "https://example.test/";
  globalThis.fetch = (async (url, init) => {
    requestedUrl = String(url);
    authorization = String((init?.headers as Record<string, string>).Authorization);
    return new Response(JSON.stringify({ trace_id: "trace/id 1", events: [] }), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  }) as typeof fetch;

  try {
    const client = new AgentGuardClient();
    await client.getTrace("trace/id 1");

    assert.equal(requestedUrl, "https://example.test/api/v1/traces/trace%2Fid%201");
    assert.equal(authorization, "Bearer ag_test");
  } finally {
    globalThis.fetch = previousFetch;
    if (previousKey === undefined) {
      delete process.env.AGENTGUARD_API_KEY;
    } else {
      process.env.AGENTGUARD_API_KEY = previousKey;
    }
    if (previousUrl === undefined) {
      delete process.env.AGENTGUARD_URL;
    } else {
      process.env.AGENTGUARD_URL = previousUrl;
    }
  }
});
