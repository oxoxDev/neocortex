# TinyHumans Neocortex Go SDK

Go client for the [TinyHumans](https://tinyhumans.ai) Neocortex memory API.

## Installation

```bash
go get github.com/tinyhumansai/neocortex-sdk-go
```

## Quick Start

```go
package main

import (
	"fmt"
	"log"
	"os"
	"time"

	"github.com/tinyhumansai/neocortex-sdk-go/tinyhumans"
)

func main() {
	client, err := tinyhumans.NewClient(
		os.Getenv("TINYHUMANS_TOKEN"),
		os.Getenv("TINYHUMANS_MODEL_ID"),
	)
	if err != nil {
		log.Fatal(err)
	}
	defer client.Close()

	// Ingest a memory
	now := float64(time.Now().Unix())
	result, err := client.IngestMemory(tinyhumans.MemoryItem{
		Key:       "user-preference-theme",
		Content:   "User prefers dark mode",
		Namespace: "preferences",
		Metadata:  map[string]interface{}{"source": "onboarding"},
		CreatedAt: &now,
		UpdatedAt: &now,
	})
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Ingested: %d, Updated: %d, Errors: %d\n",
		result.Ingested, result.Updated, result.Errors)

	// Recall memory (get LLM-friendly context)
	ctx, err := client.RecallMemory(
		"preferences",
		"What theme does the user prefer?",
		nil, // uses default options (10 chunks)
	)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Println(ctx.Context)

	// Query LLM with context (optional)
	resp, err := client.RecallWithLLM(
		"What theme does the user prefer?",
		os.Getenv("OPENAI_API_KEY"),
		tinyhumans.RecallWithLLMOptions{
			Provider: "openai",
			Model:    "gpt-4o-mini",
			Context:  ctx.Context,
		},
	)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Println(resp.Text)

	// Delete memory
	client.DeleteMemory("preferences", nil)
}
```

## API Reference

### `NewClient(token, modelID string, baseURL ...string) (*Client, error)`

Creates a new client. Base URL resolution: parameter > `TINYHUMANS_BASE_URL` env var > `https://api.tinyhumans.ai`.

### `Client.IngestMemory(item MemoryItem) (*IngestMemoryResponse, error)`

Ingest a single memory item.

### `Client.IngestMemories(items []MemoryItem) (*IngestMemoryResponse, error)`

Ingest multiple memory items.

### `Client.RecallMemory(namespace, prompt string, opts *RecallMemoryOptions) (*GetContextResponse, error)`

Retrieve relevant memory chunks as an LLM-friendly context string.

Options: `NumChunks` (default 10), `Key`, `Keys`.

### `Client.DeleteMemory(namespace string, opts *DeleteMemoryOptions) (*DeleteMemoryResponse, error)`

Delete memory items by namespace.

Options: `Key`, `Keys`, `DeleteAll`.

### `Client.RecallWithLLM(prompt, apiKey string, opts RecallWithLLMOptions) (*LLMQueryResponse, error)`

Query an LLM with optional memory context. Supported providers: `openai`, `anthropic`, `google`, or custom (via `URL`).

### `Client.Close()`

Release resources held by the client.

## LLM Providers

| Provider | Model Examples |
|----------|---------------|
| `openai` | `gpt-4o-mini`, `gpt-4o` |
| `anthropic` | `claude-3-5-sonnet-20241022` |
| `google` | `gemini-1.5-flash` |
| Custom | Any OpenAI-compatible endpoint via `URL` |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `TINYHUMANS_BASE_URL` | Override default API base URL |

## License

See repository root.
