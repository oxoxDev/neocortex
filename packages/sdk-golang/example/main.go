// Example usage of the TinyHumans Go SDK.
//
// Set environment variables: ALPHAHUMAN_TOKEN, OPENAI_API_KEY
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
		os.Getenv("ALPHAHUMAN_TOKEN"),
	)
	if err != nil {
		log.Fatal(err)
	}
	defer client.Close()

	// Ingest (upsert) a single memory
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
	fmt.Printf("Ingested: %d, Updated: %d, Errors: %d\n", result.Ingested, result.Updated, result.Errors)

	// Get LLM context
	ctx, err := client.RecallMemory("preferences", "What is the user's preference for theme?", nil)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Println(ctx.Context)

	// (Optional) Query LLM with context
	openaiKey := os.Getenv("OPENAI_API_KEY")
	if openaiKey != "" {
		resp, err := client.RecallWithLLM(
			"What is the user's preference for theme?",
			openaiKey,
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
	}

	// Delete by namespace
	_, err = client.DeleteMemory("preferences", nil)
	if err != nil {
		log.Fatal(err)
	}
}
