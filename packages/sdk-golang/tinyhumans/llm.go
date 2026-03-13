package tinyhumans

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"
)

var supportedLLMProviders = []string{"openai", "anthropic", "google"}

// queryLLM dispatches to the appropriate provider.
func queryLLM(prompt, provider, model, apiKey, context string, maxTokens *int, temperature *float64, url string) (*LLMQueryResponse, error) {
	if strings.TrimSpace(apiKey) == "" {
		return nil, fmt.Errorf("api_key is required for RecallWithLLM")
	}
	apiKey = strings.TrimSpace(apiKey)

	var text string
	var err error

	if url != "" {
		text, err = queryCustom(url, prompt, model, apiKey, context, maxTokens, temperature)
	} else {
		provider = strings.ToLower(strings.TrimSpace(provider))
		if !isSupported(provider) {
			return nil, fmt.Errorf("provider must be one of %v, got %q. For custom providers, pass the URL parameter", supportedLLMProviders, provider)
		}
		text, err = queryProvider(prompt, provider, model, apiKey, context, maxTokens, temperature)
	}

	if err != nil {
		return nil, err
	}
	return &LLMQueryResponse{Text: text}, nil
}

func isSupported(provider string) bool {
	for _, p := range supportedLLMProviders {
		if p == provider {
			return true
		}
	}
	return false
}

func queryProvider(prompt, provider, model, apiKey, context string, maxTokens *int, temperature *float64) (string, error) {
	client := &http.Client{Timeout: 60 * time.Second}

	switch provider {
	case "openai":
		return queryOpenAI(client, prompt, model, apiKey, context, maxTokens, temperature)
	case "anthropic":
		return queryAnthropic(client, prompt, model, apiKey, context, maxTokens, temperature)
	case "google":
		return queryGoogle(client, prompt, model, apiKey, context, maxTokens, temperature)
	default:
		return "", fmt.Errorf("unsupported provider: %s", provider)
	}
}

func queryOpenAI(client *http.Client, prompt, model, apiKey, context string, maxTokens *int, temperature *float64) (string, error) {
	messages := []map[string]string{}
	if context != "" {
		messages = append(messages, map[string]string{"role": "system", "content": context})
	}
	messages = append(messages, map[string]string{"role": "user", "content": prompt})

	body := map[string]interface{}{"model": model, "messages": messages}
	if maxTokens != nil {
		body["max_tokens"] = *maxTokens
	}
	if temperature != nil {
		body["temperature"] = *temperature
	}

	data, err := llmPost(client, "https://api.openai.com/v1/chat/completions", map[string]string{
		"Authorization": "Bearer " + apiKey,
		"Content-Type":  "application/json",
	}, body, "OpenAI")
	if err != nil {
		return "", err
	}

	return extractOpenAIResponse(data)
}

func queryAnthropic(client *http.Client, prompt, model, apiKey, context string, maxTokens *int, temperature *float64) (string, error) {
	mt := 1024
	if maxTokens != nil {
		mt = *maxTokens
	}

	body := map[string]interface{}{
		"model":      model,
		"max_tokens": mt,
		"messages":   []map[string]string{{"role": "user", "content": prompt}},
	}
	if context != "" {
		body["system"] = context
	}
	if temperature != nil {
		body["temperature"] = *temperature
	}

	data, err := llmPost(client, "https://api.anthropic.com/v1/messages", map[string]string{
		"x-api-key":         apiKey,
		"anthropic-version": "2023-06-01",
		"Content-Type":      "application/json",
	}, body, "Anthropic")
	if err != nil {
		return "", err
	}

	content, ok := data["content"].([]interface{})
	if !ok || len(content) == 0 {
		return "", fmt.Errorf("Anthropic: unexpected response format")
	}
	first, ok := content[0].(map[string]interface{})
	if !ok {
		return "", fmt.Errorf("Anthropic: unexpected content format")
	}
	text, ok := first["text"].(string)
	if !ok {
		return "", fmt.Errorf("Anthropic: missing text in response")
	}
	return text, nil
}

func queryGoogle(client *http.Client, prompt, model, apiKey, context string, maxTokens *int, temperature *float64) (string, error) {
	text := prompt
	if context != "" {
		text = fmt.Sprintf("Context:\n%s\n\nUser: %s", context, prompt)
	}

	body := map[string]interface{}{
		"contents": []map[string]interface{}{
			{"parts": []map[string]string{{"text": text}}},
		},
	}
	if maxTokens != nil || temperature != nil {
		genConfig := map[string]interface{}{}
		if maxTokens != nil {
			genConfig["maxOutputTokens"] = *maxTokens
		}
		if temperature != nil {
			genConfig["temperature"] = *temperature
		}
		body["generationConfig"] = genConfig
	}

	url := fmt.Sprintf("https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent?key=%s", model, apiKey)
	data, err := llmPost(client, url, map[string]string{
		"Content-Type": "application/json",
	}, body, "Google")
	if err != nil {
		return "", err
	}

	candidates, ok := data["candidates"].([]interface{})
	if !ok || len(candidates) == 0 {
		return "", fmt.Errorf("Google: unexpected response format")
	}
	candidate, ok := candidates[0].(map[string]interface{})
	if !ok {
		return "", fmt.Errorf("Google: unexpected candidate format")
	}
	contentObj, ok := candidate["content"].(map[string]interface{})
	if !ok {
		return "", fmt.Errorf("Google: missing content in response")
	}
	parts, ok := contentObj["parts"].([]interface{})
	if !ok || len(parts) == 0 {
		return "", fmt.Errorf("Google: missing parts in response")
	}
	part, ok := parts[0].(map[string]interface{})
	if !ok {
		return "", fmt.Errorf("Google: unexpected part format")
	}
	result, ok := part["text"].(string)
	if !ok {
		return "", fmt.Errorf("Google: missing text in response")
	}
	return result, nil
}

func queryCustom(url, prompt, model, apiKey, context string, maxTokens *int, temperature *float64) (string, error) {
	messages := []map[string]string{}
	if context != "" {
		messages = append(messages, map[string]string{"role": "system", "content": context})
	}
	messages = append(messages, map[string]string{"role": "user", "content": prompt})

	body := map[string]interface{}{"model": model, "messages": messages}
	if maxTokens != nil {
		body["max_tokens"] = *maxTokens
	}
	if temperature != nil {
		body["temperature"] = *temperature
	}

	client := &http.Client{Timeout: 60 * time.Second}
	data, err := llmPost(client, url, map[string]string{
		"Authorization": "Bearer " + apiKey,
		"Content-Type":  "application/json",
	}, body, "Custom provider")
	if err != nil {
		return "", err
	}

	return extractOpenAIResponse(data)
}

func extractOpenAIResponse(data map[string]interface{}) (string, error) {
	choices, ok := data["choices"].([]interface{})
	if !ok || len(choices) == 0 {
		return "", fmt.Errorf("unexpected response format: no choices")
	}
	choice, ok := choices[0].(map[string]interface{})
	if !ok {
		return "", fmt.Errorf("unexpected choice format")
	}
	msg, ok := choice["message"].(map[string]interface{})
	if !ok {
		return "", fmt.Errorf("unexpected message format")
	}
	content, ok := msg["content"].(string)
	if !ok {
		return "", fmt.Errorf("missing content in response")
	}
	return content, nil
}

func llmPost(client *http.Client, url string, headers map[string]string, body map[string]interface{}, providerName string) (map[string]interface{}, error) {
	jsonBody, err := json.Marshal(body)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	req, err := http.NewRequest("POST", url, bytes.NewReader(jsonBody))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}
	for k, v := range headers {
		req.Header.Set(k, v)
	}

	resp, err := client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("%s request failed: %w", providerName, err)
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read %s response: %w", providerName, err)
	}

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		var payload map[string]interface{}
		msg := string(respBody)
		if json.Unmarshal(respBody, &payload) == nil {
			if errObj, ok := payload["error"].(map[string]interface{}); ok {
				if m, ok := errObj["message"].(string); ok {
					msg = m
				}
			} else if m, ok := payload["message"].(string); ok {
				msg = m
			}
		}
		return nil, &TinyHumanError{
			Message: fmt.Sprintf("%s API error: %s", providerName, msg),
			Status:  resp.StatusCode,
		}
	}

	var data map[string]interface{}
	if err := json.Unmarshal(respBody, &data); err != nil {
		return nil, fmt.Errorf("failed to parse %s response: %w", providerName, err)
	}
	return data, nil
}
