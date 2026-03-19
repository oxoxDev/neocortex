# Neocortex Codex Plugin

Codex MCP plugin for **Neocortex-powered long‑term memory**.

This package provides a small MCP server and TypeScript helpers so the [Codex](https://github.com/sting8k/opencode-codex-plugin) environment can call Neocortex tools to **save**, **recall**, and **delete** persistent memory, similar in spirit to `codex-extra-memory` but backed by Neocortex instead of a local SQLite/LanceDB store.

## Features

- **MCP server for Codex** — exposes three tools:
  - `neocortex_save_memory`
  - `neocortex_recall_memory`
  - `neocortex_delete_memory`
- **Shared client** — reuses the same `NeocortexMemoryClient` and types as the other Neocortex plugins.
- **Simple bootstrap** — one helper (`runNeocortexMcpServerFromEnv`) you can reference from your Codex MCP configuration.

## Install

```bash
npm install @neocortex/plugin-codex
```

## Quick Start — MCP Server for Codex

1. **Install the package** into the workspace that Codex uses for MCP servers:

```bash
npm install @neocortex/plugin-codex
```

2. **Configure an MCP server** in your Codex config (typically `config.toml` under `$CODEX_HOME` or your workspace), modelled after the `codex-extra-memory` examples:

```toml
[mcp_servers.neocortex_memory]
command = "node"
args = ["./node_modules/@neocortex/plugin-codex/dist/index.js"]
required = true
enabled = true
startup_timeout_sec = 20
tool_timeout_sec = 90
enabled_tools = [
  "neocortex_save_memory",
  "neocortex_recall_memory",
  "neocortex_delete_memory",
]
```

Then set environment variables for the MCP process:

- `ALPHAHUMAN_API_KEY` (required): Neocortex/Alphahuman API key or JWT.
- `ALPHAHUMAN_BASE_URL` (optional): Override Neocortex base URL; defaults to the same staging URL used by other Neocortex plugins.

3. When Codex starts, it will:

- Launch the MCP server via `node dist/index.js`.
- Discover the tools:
  - `neocortex_save_memory`
  - `neocortex_recall_memory`
  - `neocortex_delete_memory`
- Allow Codex agents, commands, or tools to call these MCP tools.

## Programmatic Usage

You can also use the adapter directly from TypeScript/Node without Codex:

```ts
import { CodexNeocortexMemory } from "@neocortex/plugin-codex";

const memory = new CodexNeocortexMemory({
  token: process.env.ALPHAHUMAN_API_KEY!,
  baseUrl: process.env.ALPHAHUMAN_BASE_URL, // optional
  defaultNamespace: "my-workspace",
});

// Save memory
await memory.saveMemory({
  key: "preferred_editor",
  content: "The user's preferred editor is VS Code.",
});

// Recall memory
const recalled = await memory.recallMemory({
  query: "What is the user's preferred editor?",
});

console.log("Recalled context:", recalled.context);
```

Internally, this uses the shared `NeocortexMemoryClient` to call Neocortex’s `/v1/memory/*` API.


## Notes

- The MCP server uses `@modelcontextprotocol/sdk`’s `McpServer` + `StdioServerTransport` and registers tools using `zod` schemas, mirroring the Claude Code and other Neocortex plugins.
- Credentials never flow through tool inputs; all sensitive configuration is provided via environment variables when the MCP server process is launched.

