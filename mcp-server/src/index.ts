#!/usr/bin/env node

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { AgentGuardClient } from "./client.js";
import { tools } from "./tools.js";

const server = new McpServer({
  name: "agentguard",
  version: "0.1.0",
});

let client: AgentGuardClient;

try {
  client = new AgentGuardClient();
} catch (err) {
  console.error((err as Error).message);
  process.exit(1);
}

// Register each tool with the MCP server
for (const tool of tools) {
  // Build a Zod schema from the JSON Schema properties
  const shape: Record<string, z.ZodTypeAny> = {};
  const required = new Set(tool.inputSchema.required ?? []);

  for (const [key, prop] of Object.entries(tool.inputSchema.properties)) {
    const p = prop as { type: string; description?: string };
    let field: z.ZodTypeAny;
    if (p.type === "number") {
      field = z.number().describe(p.description ?? "");
    } else {
      field = z.string().describe(p.description ?? "");
    }
    shape[key] = required.has(key) ? field : field.optional();
  }

  const toolName = tool.name;
  const handler = tool.handler;

  server.tool(toolName, tool.description, shape, async (args) => {
    try {
      const text = await handler(client, args as Record<string, unknown>);
      return { content: [{ type: "text" as const, text }] };
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      return {
        content: [{ type: "text" as const, text: `Error: ${message}` }],
        isError: true,
      };
    }
  });
}

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((err) => {
  console.error("Fatal:", err);
  process.exit(1);
});
