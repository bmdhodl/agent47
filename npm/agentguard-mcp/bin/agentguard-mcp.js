#!/usr/bin/env node
const { spawnSync } = require("node:child_process");

const python = process.env.PYTHON || (process.platform === "win32" ? "py" : "python3");
const moduleArgs = process.platform === "win32" && python === "py"
  ? ["-3", "-m", "agentguard_mcp"]
  : ["-m", "agentguard_mcp"];

if (process.env.AGENTGUARD_MCP_SKIP_PIP_INSTALL !== "1") {
  const pipArgs = process.platform === "win32" && python === "py"
    ? ["-3", "-m", "pip", "install", "--upgrade", "agentguard-mcp"]
    : ["-m", "pip", "install", "--upgrade", "agentguard-mcp"];
  const install = spawnSync(python, pipArgs, { stdio: "inherit" });
  if (install.status !== 0) {
    process.exit(install.status || 1);
  }
}

const result = spawnSync(python, moduleArgs.concat(process.argv.slice(2)), {
  stdio: "inherit",
});

process.exit(result.status || 0);
