#!/usr/bin/env node

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { AgentGuardClient } from "./client.js";
import { buildToolShape } from "./schema.js";
import { tools } from "./tools.js";

const server = new McpServer({
  name: "agentguard",
  version: "0.2.1",
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
  const shape = buildToolShape(tool.inputSchema.properties, tool.inputSchema.required);

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
