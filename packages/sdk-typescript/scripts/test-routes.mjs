#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const pkgRoot = path.resolve(__dirname, "..");

function loadEnvFile(filePath) {
  if (!fs.existsSync(filePath)) return;
  const lines = fs.readFileSync(filePath, "utf8").split(/\r?\n/);
  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#") || !line.includes("=")) continue;
    const i = line.indexOf("=");
    const key = line.slice(0, i).trim();
    let value = line.slice(i + 1).trim();
    if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    }
    if (!(key in process.env)) {
      process.env[key] = value;
    }
  }
}

const envFile = process.env.ENV_FILE || path.join(pkgRoot, ".env");
loadEnvFile(envFile);

const token = process.env.ALPHAHUMAN_TOKEN || process.env.TINYHUMANS_TOKEN;
if (!token) {
  console.error("Missing token. Set ALPHAHUMAN_TOKEN or TINYHUMANS_TOKEN.");
  process.exit(2);
}

const baseUrl = process.env.TINYHUMANS_BASE_URL || process.env.ALPHAHUMAN_BASE_URL;
const { AlphahumanMemoryClient } = await import(path.join(pkgRoot, "dist", "index.js"));
const client = new AlphahumanMemoryClient({ token, baseUrl });

const ts = Date.now();
const namespace = `sdk-ts-routes-${ts}`;
const docSingle = `ts-doc-single-${ts}`;
const docBatch1 = `ts-doc-batch-1-${ts}`;
const docBatch2 = `ts-doc-batch-2-${ts}`;

const results = [];
let maybeJobId;

async function run(name, fn, optional = false) {
  try {
    const data = await fn();
    results.push({ name, ok: true, msg: "ok" });
    return data;
  } catch (err) {
    if (optional) {
      const message = err instanceof Error ? err.message : String(err);
      results.push({ name, ok: true, msg: `optional-skip: ${message}` });
      return undefined;
    }
    const message = err instanceof Error ? err.message : String(err);
    results.push({ name, ok: false, msg: message });
    return undefined;
  }
}

try {
  await run("insertMemory", () =>
    client.insertMemory({
      title: "TS Route Test Memory",
      content: "typescript route test memory",
      namespace,
      sourceType: "doc",
      metadata: { source: "sdk-typescript-route-test" },
      documentId: `${docSingle}-memory`,
    }),
  );

  await run("queryMemory", () =>
    client.queryMemory({
      query: "what memory was stored",
      namespace,
      maxChunks: 5,
      includeReferences: true,
    }),
  );

  await run("insertDocument", () =>
    client.insertDocument({
      title: "TS Route Test Single",
      content: "Single document for route test",
      namespace,
      sourceType: "doc",
      metadata: { source: "sdk-typescript-route-test", kind: "single" },
      documentId: docSingle,
    }),
  );

  const batchRes = await run("insertDocumentsBatch", () =>
    client.insertDocumentsBatch({
      items: [
        {
          title: "TS Route Test Batch 1",
          content: "Batch document 1",
          namespace,
          documentId: docBatch1,
        },
        {
          title: "TS Route Test Batch 2",
          content: "Batch document 2",
          namespace,
          documentId: docBatch2,
        },
      ],
    }),
  );

  if (batchRes?.data?.jobId) {
    maybeJobId = batchRes.data.jobId;
  } else if (Array.isArray(batchRes?.data?.accepted)) {
    for (const row of batchRes.data.accepted) {
      if (row?.jobId) {
        maybeJobId = row.jobId;
        break;
      }
    }
  }

  await run("listDocuments", () => client.listDocuments({ namespace, limit: 20, offset: 0 }));
  await run("getDocument", () => client.getDocument({ documentId: docSingle, namespace }));

  await run("queryMemoryContext", () =>
    client.queryMemoryContext({
      query: "summarize route test docs",
      namespace,
      includeReferences: true,
      maxChunks: 5,
      documentIds: [docSingle],
    }),
  );

  await run("chatMemoryContext", () =>
    client.chatMemoryContext({
      messages: [{ role: "user", content: "Summarize what the route test inserted." }],
      temperature: 0,
      maxTokens: 128,
    }),
    true,
  );

  await run("recordInteractions", () =>
    client.recordInteractions({
      namespace,
      entityNames: ["TS-ROUTE-TEST-A", "TS-ROUTE-TEST-B"],
      description: "typescript route test interactions",
      interactionLevel: "engage",
    }),
  );

  await run("recallThoughts", () =>
    client.recallThoughts({ namespace, maxChunks: 5, thoughtPrompt: "Reflect on stored docs" }),
  );

  await run("getGraphSnapshot", () =>
    client.getGraphSnapshot({ namespace, mode: "latest_chunks", limit: 10, seed_limit: 3 }),
    true,
  );

  await run("chatMemory", () =>
    client.chatMemory({
      messages: [{ role: "user", content: "Reply with ok" }],
      temperature: 0,
      maxTokens: 64,
    }),
    true,
  );

  await run("interactMemory", () =>
    client.interactMemory({
      namespace,
      entityNames: ["TS-ROUTE-TEST-A", "TS-ROUTE-TEST-B"],
      description: "typescript route test interact",
      interactionLevel: "engage",
      timestamp: Math.floor(Date.now() / 1000),
    }),
  );

  await run("recallMemory", () => client.recallMemory({ namespace, maxChunks: 5 }));
  await run("recallMemories", () => client.recallMemories({ namespace, topK: 5, minRetention: 0 }));

  if (maybeJobId) {
    await run("getIngestionJob", () => client.getIngestionJob(maybeJobId));
  } else {
    results.push({ name: "getIngestionJob", ok: true, msg: "optional-skip: no jobId returned by inserts" });
  }

} finally {
  await run("deleteDocument(single)", () => client.deleteDocument({ documentId: docSingle, namespace }), true);
  await run("deleteDocument(batch1)", () => client.deleteDocument({ documentId: docBatch1, namespace }), true);
  await run("deleteDocument(batch2)", () => client.deleteDocument({ documentId: docBatch2, namespace }), true);
  await run("deleteMemory", () => client.deleteMemory({ namespace }), true);
}

console.log("\nRoute smoke test results (sdk-typescript):");
for (const row of results) {
  console.log(`- ${row.ok ? "PASS" : "FAIL"} ${row.name}: ${row.msg}`);
}

const failed = results.filter((row) => !row.ok);
if (failed.length > 0) {
  console.error(`\nFailed checks: ${failed.length}`);
  process.exit(1);
}

console.log(`\nAll required checks passed: ${results.length}`);
