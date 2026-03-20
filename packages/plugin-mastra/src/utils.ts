import type { MastraTool } from "./types";

const DEFAULT_BASE_URL = "https://staging-api.alphahuman.xyz";

export function getEnv(key: string): string | undefined {
  try {
    const g = typeof globalThis !== "undefined" ? globalThis : (undefined as unknown as Record<string, unknown>);
    const env = (g as { process?: { env?: Record<string, string | undefined> } }).process?.env;
    return env?.[key];
  } catch {
    return undefined;
  }
}

export function resolveBaseUrl(explicit?: string): string {
  const baseUrl = explicit ?? getEnv("ALPHAHUMAN_BASE_URL") ?? DEFAULT_BASE_URL;
  return baseUrl.replace(/\/+$/, "");
}

/** Lightweight JSON schema helper for simple “object with properties”. */
export function objectSchema(input: {
  description?: string;
  properties: Record<string, Record<string, unknown>>;
  required?: string[];
}): Record<string, unknown> {
  return {
    type: "object",
    description: input.description,
    properties: input.properties,
    required: input.required ?? [],
  };
}

export const NEOCORTEX_MASTRA_TOOL_SCHEMAS = {
  neocortex_save_memory: {
    name: "neocortex_save_memory",
    description: "Save a piece of important information into long-term memory.",
    parameters: objectSchema({
      properties: {
        namespace: { type: "string", description: "Optional namespace override." },
        key: { type: "string", description: "Short key/title for the memory." },
        content: { type: "string", description: "The content to remember." },
        metadata: { type: "object", description: "Optional metadata object." },
      },
      required: ["key", "content"],
    }),
  },
  neocortex_recall_memory: {
    name: "neocortex_recall_memory",
    description: "Recall relevant long-term memory for the given query.",
    parameters: objectSchema({
      properties: {
        namespace: { type: "string", description: "Optional namespace override." },
        query: { type: "string", description: "Natural-language query for memory." },
        max_chunks: { type: "integer", description: "Max number of chunks to retrieve." },
      },
      required: ["query"],
    }),
  },
  neocortex_delete_memory: {
    name: "neocortex_delete_memory",
    description: "Delete all memory in a namespace (admin delete).",
    parameters: objectSchema({
      properties: {
        namespace: { type: "string", description: "Namespace to delete. If omitted, backend decides scope." },
      },
      required: [],
    }),
  },
} as const satisfies Record<string, Omit<MastraTool, "execute">>;

