import { NeocortexMemoryClient } from "./client";
import { createTool } from "@mastra/core/tools";
import { z } from "zod";
import type {
  DeleteMemoryInput,
  MastraTool,
  NeocortexConfig,
  RecallMemoryInput,
  SaveMemoryInput,
} from "./types";
import { NEOCORTEX_MASTRA_TOOL_SCHEMAS } from "./utils";

export * from "./types";
export * from "./utils";

export interface MastraNeocortexConfig extends NeocortexConfig {
  /** Default namespace used when tool input does not specify one. */
  defaultNamespace?: string;
}

/**
 * createNeocortexMastraTools
 *
 * Mastra-native tools created via `createTool()` (similar ergonomics to Agno's Toolkit:
 * you get ready-to-register tools).
 *
 * Notes:
 * - Tools are bound to the provided credentials; credentials never flow through tool inputs.
 * - If you want tool names in traces/streams to match tool IDs, register as:
 *   `tools: { [tool.id]: tool }`.
 */
export function createNeocortexMastraTools(config: MastraNeocortexConfig) {
  const memory = new MastraNeocortexMemory(config);

  const neocortexSaveMemory = createTool({
    id: NEOCORTEX_MASTRA_TOOL_SCHEMAS.neocortex_save_memory.name,
    description: NEOCORTEX_MASTRA_TOOL_SCHEMAS.neocortex_save_memory.description,
    inputSchema: z.object({
      namespace: z.string().optional().describe("Optional namespace override."),
      key: z.string().describe("Short key/title for the memory."),
      content: z.string().describe("The content to remember."),
      metadata: z.record(z.unknown()).optional().describe("Optional metadata object."),
    }),
    outputSchema: z.object({
      ok: z.literal(true),
      namespace: z.string(),
      message: z.string(),
    }),
    execute: async (inputData) => memory.saveMemory(inputData),
  });

  const neocortexRecallMemory = createTool({
    id: NEOCORTEX_MASTRA_TOOL_SCHEMAS.neocortex_recall_memory.name,
    description: NEOCORTEX_MASTRA_TOOL_SCHEMAS.neocortex_recall_memory.description,
    inputSchema: z.object({
      namespace: z.string().optional().describe("Optional namespace override."),
      query: z.string().describe("Natural-language query for memory."),
      max_chunks: z.number().int().optional().describe("Max number of chunks to retrieve."),
    }),
    outputSchema: z.object({
      ok: z.literal(true),
      namespace: z.string(),
      context: z.string(),
      raw: z.unknown(),
    }),
    execute: async (inputData) => memory.recallMemory(inputData),
  });

  const neocortexDeleteMemory = createTool({
    id: NEOCORTEX_MASTRA_TOOL_SCHEMAS.neocortex_delete_memory.name,
    description: NEOCORTEX_MASTRA_TOOL_SCHEMAS.neocortex_delete_memory.description,
    inputSchema: z.object({
      namespace: z.string().optional().describe("Namespace to delete."),
    }),
    outputSchema: z.object({
      ok: z.literal(true),
      namespace: z.string().optional(),
      message: z.string(),
      raw: z.unknown(),
    }),
    execute: async (inputData) => memory.deleteMemory(inputData),
  });

  return { memory, neocortexSaveMemory, neocortexRecallMemory, neocortexDeleteMemory };
}

/**
 * MastraNeocortexMemory
 *
 * A lightweight adapter that exposes Neocortex (Alphahuman) memory as tools in a
 * Mastra-friendly shape: `{ name, description, parameters, execute }`.
 *
 * If Mastra expects a different tool signature, you can still use the provided
 * `NEOCORTEX_MASTRA_TOOL_SCHEMAS` + call `saveMemory/recallMemory/deleteMemory` directly.
 */
export class MastraNeocortexMemory {
  private readonly client: NeocortexMemoryClient;
  private readonly defaultNamespace: string;

  constructor(config: MastraNeocortexConfig) {
    this.client = new NeocortexMemoryClient(config);
    this.defaultNamespace = config.defaultNamespace?.trim() || "default";
  }

  async saveMemory(input: SaveMemoryInput): Promise<{ ok: true; namespace: string; message: string }> {
    const namespace = input.namespace?.trim() || this.defaultNamespace;
    const res = await this.client.insertMemory({
      title: input.key,
      content: input.content,
      namespace,
      metadata: input.metadata,
      sourceType: "doc",
    });
    const status = (res as any)?.data?.status ?? "completed";
    return {
      ok: true,
      namespace,
      message: `Saved memory '${input.key}' in namespace '${namespace}' (status=${status}).`,
    };
  }

  async recallMemory(input: RecallMemoryInput): Promise<{ ok: true; namespace: string; context: string; raw: unknown }> {
    const namespace = input.namespace?.trim() || this.defaultNamespace;
    const res = await this.client.queryMemory({
      query: input.query,
      namespace,
      maxChunks: input.max_chunks ?? 10,
    });
    const data = res.data;
    const context = data.llmContextMessage || data.response;
    if (typeof context === "string" && context.trim()) {
      return { ok: true, namespace, context: context.trim(), raw: data };
    }

    const chunks = data.context?.chunks ?? [];
    const texts: string[] = [];
    for (const chunk of chunks) {
      if (chunk && typeof chunk === "object") {
        const text = (chunk as any).content ?? (chunk as any).text ?? (chunk as any).body ?? "";
        if (typeof text === "string" && text.trim()) texts.push(text.trim());
      }
    }
    return {
      ok: true,
      namespace,
      context: texts.length ? texts.join("\n\n") : "No relevant memories found.",
      raw: data,
    };
  }

  async deleteMemory(input: DeleteMemoryInput): Promise<{ ok: true; namespace?: string; message: string; raw: unknown }> {
    const namespace = input.namespace?.trim() || undefined;
    const res = await this.client.deleteMemory({ namespace });
    return {
      ok: true,
      namespace,
      message: res.data?.message || "Memory deleted.",
      raw: res.data,
    };
  }

  /**
   * Tools you can register with Mastra.
   *
   * The names and schemas are stable; credentials never flow through tool params.
   */
  getTools(): Array<MastraTool<any, any>> {
    return [
      {
        ...NEOCORTEX_MASTRA_TOOL_SCHEMAS.neocortex_save_memory,
        execute: (params: SaveMemoryInput) => this.saveMemory(params),
      },
      {
        ...NEOCORTEX_MASTRA_TOOL_SCHEMAS.neocortex_recall_memory,
        execute: (params: RecallMemoryInput) => this.recallMemory(params),
      },
      {
        ...NEOCORTEX_MASTRA_TOOL_SCHEMAS.neocortex_delete_memory,
        execute: (params: DeleteMemoryInput) => this.deleteMemory(params),
      },
    ];
  }
}

