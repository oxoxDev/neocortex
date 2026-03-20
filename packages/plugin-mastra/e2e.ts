/**
 * E2E for plugin-mastra using real Mastra Agent + Neocortex tools.
 *
 * Required env:
 *   ALPHAHUMAN_API_KEY
 *
 * Optional env:
 *   ALPHAHUMAN_BASE_URL
 *   OPENAI_API_KEY (recommended so Mastra can run the LLM + call tools)
 *
 * Run from this package directory:
 *   npx tsx e2e.ts
 */

import { Agent } from "@mastra/core/agent";
import { createNeocortexMastraTools } from "./src/index";

function getEnv(name: string): string {
  try {
    const g =
      typeof globalThis !== "undefined"
        ? globalThis
        : ((undefined as unknown) as Record<string, unknown>);
    const env = (g as { process?: { env?: Record<string, string | undefined> } }).process
      ?.env;
    return env?.[name] ?? "";
  } catch {
    return "";
  }
}

const ALPHAHUMAN_API_KEY = getEnv("ALPHAHUMAN_API_KEY");
const ALPHAHUMAN_BASE_URL = getEnv("ALPHAHUMAN_BASE_URL");
const OPENAI_API_KEY = getEnv("OPENAI_API_KEY");

if (!ALPHAHUMAN_API_KEY) {
  throw new Error("Missing ALPHAHUMAN_API_KEY");
}

const namespace = `mastra-e2e-${Date.now()}`;

async function run() {
  console.log("Mastra plugin E2E");
  console.log("  namespace:", namespace);
  console.log("  ALPHAHUMAN_BASE_URL:", ALPHAHUMAN_BASE_URL || "(default)");
  console.log("  OPENAI_API_KEY:", OPENAI_API_KEY ? "set" : "not set");
  console.log("---");

  const { neocortexSaveMemory, neocortexRecallMemory, neocortexDeleteMemory } =
    createNeocortexMastraTools({
      token: ALPHAHUMAN_API_KEY,
      baseUrl: ALPHAHUMAN_BASE_URL || undefined,
      defaultNamespace: namespace,
    });

  const agent = new Agent({
    id: "neocortex-mastra-e2e",
    name: "Neocortex Mastra E2E Agent",
    instructions: [
      "You are a test agent.",
      "When the user states a preference or important fact, call neocortex_save_memory.",
      "When the user asks about past preferences/facts, call neocortex_recall_memory and answer using its context.",
      "Keep answers short and direct.",
    ].join("\n"),
    model: "openai/gpt-5.1",
    tools: {
      // Use tool IDs as keys so toolName matches IDs in traces/streams
      [neocortexSaveMemory.id]: neocortexSaveMemory,
      [neocortexRecallMemory.id]: neocortexRecallMemory,
      [neocortexDeleteMemory.id]: neocortexDeleteMemory,
    },
  });

  // Turn 1: should trigger neocortex_save_memory
  const msg1 = "Please remember: my preferred drink is coffee.";
  console.log("User:", msg1);
  const r1 = await agent.generate(msg1, {
    memory: { thread: namespace, resource: "plugin-mastra-e2e" },
  });
  console.log("Agent:", r1.text);

  // Turn 2: should trigger neocortex_recall_memory
  const msg2 = "What is my preferred drink?";
  console.log("\nUser:", msg2);
  const r2 = await agent.generate(msg2, {
    memory: { thread: namespace, resource: "plugin-mastra-e2e" },
  });
  console.log("Agent:", r2.text);

  console.log("\n---");
  console.log(
    "If tools were not called, ensure your LLM provider is configured (e.g. set OPENAI_API_KEY) and rerun."
  );
}

run().catch((e) => {
  console.error("E2E failed:", e);
  throw e;
});