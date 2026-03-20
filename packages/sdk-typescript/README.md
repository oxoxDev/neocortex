# @alphahuman/memory-sdk

TypeScript / JavaScript SDK for the [Alphahuman Memory API](https://alphahuman.xyz), aligned with the backend API: insert, query, chat, documents, admin/delete, recall, thoughts, interact, and more.
## Requirements

- Node.js ≥ 18 (uses native `fetch`)

## Install

```bash
npm install @alphahuman/memory-sdk
```

## Quick start

```typescript
import { AlphahumanMemoryClient } from '@alphahuman/memory-sdk';

const client = new AlphahumanMemoryClient({ token: 'your-api-key' });

// Insert (ingest) a document into memory
const insertResult = await client.insertMemory({
  title: 'User preference',
  content: 'User prefers dark mode',
  namespace: 'preferences',
});
console.log(insertResult.data); // { status, stats, usage? }

// Query memory via RAG
const queryResult = await client.queryMemory({
  query: 'What does the user prefer?',
  namespace: 'preferences',
  maxChunks: 10,
});
console.log(queryResult.data.context, queryResult.data.response);

// Recall context from Master node
const recallResult = await client.recallMemory({ namespace: 'preferences', maxChunks: 10 });

// Recall memories from Ebbinghaus bank
const memoriesResult = await client.recallMemories({ namespace: 'preferences', topK: 5 });

// Delete memory (admin)
await client.deleteMemory({ namespace: 'preferences' });
```

## API reference

### `new AlphahumanMemoryClient(config)`

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `config.token` | `string` | ✓ | API key or JWT |
| `config.baseUrl` | `string` | | Override API URL. If not set, uses `TINYHUMANS_BASE_URL` env or default `https://api.tinyhumans.ai` |

### `client.insertMemory(params)`

Insert a document into memory. **POST /memory/insert**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | `string` | ✓ | Document title |
| `content` | `string` | ✓ | Document content |
| `namespace` | `string` | ✓ | Namespace |
| `sourceType` | `'doc' \| 'chat' \| 'email'` | | Default `'doc'` |
| `metadata` | `object` | | Optional metadata |
| `priority` | `'high' \| 'medium' \| 'low'` | | Optional priority |
| `createdAt` | `number` | | Unix timestamp (seconds) |
| `updatedAt` | `number` | | Unix timestamp (seconds) |
| `documentId` | `string` | | Optional document ID |

Returns `InsertMemoryResponse` with `data: { status, stats, usage? }`.

### `client.queryMemory(params)`

Query memory via RAG. **POST /memory/query**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | `string` | ✓ | Query string |
| `includeReferences` | `boolean` | | Include references in response |
| `namespace` | `string` | | Scope to namespace |
| `maxChunks` | `number` | | 1–200 |
| `documentIds` | `string[]` | | Filter by document IDs |
| `llmQuery` | `string` | | Optional LLM query |

Returns `QueryMemoryResponse` with `data: { context?, usage?, cached, llmContextMessage?, response? }`.

### `client.deleteMemory(params?)`

Delete memory (admin). **POST /memory/admin/delete**

| Field | Type | Description |
|-------|------|-------------|
| `namespace` | `string` | Optional namespace to scope deletion |

Returns `DeleteMemoryResponse` with `data: { status, userId, namespace?, nodesDeleted, message }`.

### `client.recallMemory(params?)`

Recall context from Master node. **POST /memory/recall**

| Field | Type | Description |
|-------|------|-------------|
| `namespace` | `string` | Optional namespace |
| `maxChunks` | `number` | Positive integer |

Returns `RecallMemoryResponse` with `data: { context?, usage?, cached, response?, latencySeconds?, counts? }`.

### `client.recallMemories(params?)`

Recall memories from Ebbinghaus bank. **POST /memory/memories/recall**

| Field | Type | Description |
|-------|------|-------------|
| `namespace` | `string` | Optional namespace |
| `topK` | `number` | Positive number |
| `minRetention` | `number` | Non-negative number |
| `asOf` | `number` | Timestamp |

Returns `RecallMemoriesResponse` with `data: { memories }`.

### `client.chatMemory(params)`

Chat with DeltaNet memory cache. **POST /memory/chat**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `messages` | `ChatMessage[]` | ✓ | List of messages `[{role, content}]` |
| `temperature` | `number` | | Optional temperature |
| `maxTokens` | `number` | | Optional max completion tokens |

Returns `ChatMemoryResponse`.

### `client.recallThoughts(params?)`

Generate reflective thoughts. **POST /memory/memories/thoughts**

| Field | Type | Description |
|-------|------|-------------|
| `namespace` | `string` | Optional namespace |
| `thoughtPrompt` | `string` | Optional custom LLM prompt |
| `maxChunks` | `number` | Number of chunks to recall |

Returns `RecallThoughtsResponse`.

### `client.insertDocument(params)`

Ingest a single memory document. **POST /memory/documents**

Supports the same fields as `insertMemory` (`title`, `content`, `namespace`, optional `sourceType`, `metadata`, `priority`, `createdAt`, `updatedAt`, `documentId`).

### `client.insertDocumentsBatch(params)`

Ingest multiple memory documents in batch. **POST /memory/documents/batch**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `items` | `{ title: string; content: string; namespace: string; ... }[]` | ✓ | Document items |

Returns `InsertDocumentsBatchResponse`.

### `client.listDocuments(params?)`

List ingested memory documents. **GET /memory/documents**

| Field | Type | Description |
|-------|------|-------------|
| `namespace` | `string` | Optional namespace |
| `limit` | `number` | Optional page size |
| `offset` | `number` | Optional page offset |

Returns `ListDocumentsResponse`.

### `client.getDocument(params)`

Get details for a memory document. **GET /memory/documents/:documentId**

| Field | Type | Description |
|-------|------|-------------|
| `documentId` | `string` | Required |
| `namespace` | `string` | Optional namespace |

Returns `GetDocumentResponse`.

### `client.deleteDocument(params)`

Delete a memory document. **DELETE /memory/documents/:documentId**

| Field | Type | Description |
|-------|------|-------------|
| `documentId` | `string` | Required |
| `namespace` | `string` | Required |

Returns `DeleteMemoryResponse`.

### `client.queryMemoryContext(params)`

Query memory context. **POST /memory/queries**

| Field | Type | Description |
|-------|------|-------------|
| `query` | `string` | ✓ Query string |
| `includeReferences` | `boolean` | Include references in response |
| `namespace` | `string` | Optional namespace |
| `maxChunks` | `number` | Optional chunk limit |
| `documentIds` | `string[]` | Optional document filters |
| `recallOnly` | `boolean` | Recall-only mode |
| `llmQuery` | `string` | Optional LLM query override |

Returns `QueryMemoryResponse`.

### `client.chatMemoryContext(params)`

Chat with memory context. **POST /memory/conversations**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `messages` | `[{ role: string; content: string }]` | ✓ | Conversation messages |
| `temperature` | `number` | | Optional temperature |
| `maxTokens` | `number` | | Optional token limit |

Returns `ChatMemoryResponse`.

### `client.recordInteractions(params)`

Record interaction signals. **POST /memory/interactions**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `namespace` | `string` | ✓ | Namespace |
| `entityNames` | `string[]` | ✓ | Entity names |
| `description` | `string` | | Optional description |
| `interactionLevel` | `'view' \| 'read' \| 'react' \| 'engage' \| 'create'` | | Optional interaction level |
| `interactionLevels` | same union array | | Optional multiple interaction levels |

Returns `InteractMemoryResponse`.

### `client.getIngestionJob(jobId)`

Get memory ingestion job status. **GET /memory/ingestion/jobs/:jobId**

Returns `GetIngestionJobResponse`.

### `client.getGraphSnapshot(params?)`

Get admin graph snapshot. **GET /memory/admin/graph-snapshot**

| Field | Type | Description |
|-------|------|-------------|
| `namespace` | `string` | Optional namespace |
| `mode` | `'master' \| 'latest_chunks'` | Optional graph mode |
| `limit` | `number` | Optional limit |
| `seed_limit` | `number` | Optional seed limit |

Returns `GetGraphSnapshotResponse`.


## Error handling

All API errors throw `AlphahumanError` (extends `Error`) with `status` (HTTP status code) and `body` (parsed response when available).

```typescript
import { AlphahumanError } from '@alphahuman/memory-sdk';

try {
  await client.queryMemory({ query: 'hello' });
} catch (err) {
  if (err instanceof AlphahumanError) {
    console.error(err.status, err.message);
  }
}
```

## Tests

```bash
npm test
```
