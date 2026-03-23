package tinyhumans

import (
	"errors"
)

// ChatMemory sends a chat request with memory context.
// POST /memory/chat
func (c *Client) ChatMemory(messages []ChatMessage, opts *ChatMemoryOptions) (map[string]interface{}, error) {
	if len(messages) == 0 {
		return nil, errors.New("messages must be a non-empty list")
	}
	for _, m := range messages {
		if m.Role == "" {
			return nil, errors.New("each message requires a non-empty role")
		}
		if m.Content == "" {
			return nil, errors.New("each message requires non-empty content")
		}
	}

	body := map[string]interface{}{
		"messages": messages,
	}
	if opts != nil {
		if opts.Temperature != nil {
			body["temperature"] = *opts.Temperature
		}
		if opts.MaxTokens != nil {
			body["maxTokens"] = *opts.MaxTokens
		}
	}

	return c.send("POST", "/memory/chat", body)
}

// ChatMemoryContext sends a chat request via the conversations endpoint.
// POST /memory/conversations
func (c *Client) ChatMemoryContext(messages []ChatMessage, opts *ChatMemoryOptions) (map[string]interface{}, error) {
	if len(messages) == 0 {
		return nil, errors.New("messages must be a non-empty list")
	}

	body := map[string]interface{}{
		"messages": messages,
	}
	if opts != nil {
		if opts.Temperature != nil {
			body["temperature"] = *opts.Temperature
		}
		if opts.MaxTokens != nil {
			body["maxTokens"] = *opts.MaxTokens
		}
	}

	return c.send("POST", "/memory/conversations", body)
}
