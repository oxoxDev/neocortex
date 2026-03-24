package xyz.tinyhumans.sdk;

import xyz.tinyhumans.sdk.internal.Json;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.Map;

/**
 * Client for the TinyHuman Memory API.
 * <p>
 * Requires Java 11+. Zero runtime dependencies.
 */
public class TinyHumansMemoryClient implements AutoCloseable {

    private static final String DEFAULT_BASE_URL = "https://api.tinyhumans.ai";
    private static final String TINYHUMANS_BASE_URL = "TINYHUMANS_BASE_URL";

    private final String baseUrl;
    private final String token;
    private final HttpClient httpClient;

    public TinyHumansMemoryClient(String token) {
        this(token, null);
    }

    public TinyHumansMemoryClient(String token, String baseUrl) {
        if (token == null || token.trim().isEmpty()) {
            throw new IllegalArgumentException("token is required");
        }
        this.token = token;

        String resolved = baseUrl;
        if (resolved == null || resolved.isEmpty()) {
            resolved = System.getenv(TINYHUMANS_BASE_URL);
        }
        if (resolved == null || resolved.isEmpty()) {
            resolved = DEFAULT_BASE_URL;
        }
        this.baseUrl = resolved.replaceAll("/+$", "");

        this.httpClient = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(30))
                .build();
    }

    /** Insert (ingest) a document into memory. POST /memory/insert */
    public InsertMemoryResponse insertMemory(InsertMemoryParams params) {
        Map<String, Object> body = params.toMap();
        Map<String, Object> response = post("/memory/insert", body);
        return InsertMemoryResponse.fromMap(response);
    }

    /** Recall context from Master node. POST /memory/recall */
    public RecallMemoryResponse recallMemory(RecallMemoryParams params) {
        Map<String, Object> body = params.toMap();
        Map<String, Object> response = post("/memory/recall", body);
        return RecallMemoryResponse.fromMap(response);
    }

    /** Delete memory (admin). POST /memory/admin/delete */
    public DeleteMemoryResponse deleteMemory(DeleteMemoryParams params) {
        Map<String, Object> body = params.toMap();
        Map<String, Object> response = post("/memory/admin/delete", body);
        return DeleteMemoryResponse.fromMap(response);
    }

    /** Query memory via RAG. POST /memory/query */
    public QueryMemoryResponse queryMemory(QueryMemoryParams params) {
        Map<String, Object> body = params.toMap();
        Map<String, Object> response = post("/memory/query", body);
        return QueryMemoryResponse.fromMap(response);
    }

    /** Recall memories from Ebbinghaus bank. POST /memory/memories/recall */
    public RecallMemoriesResponse recallMemories(RecallMemoriesParams params) {
        Map<String, Object> body = params.toMap();
        Map<String, Object> response = post("/memory/memories/recall", body);
        return RecallMemoriesResponse.fromMap(response);
    }

    @Override
    public void close() {
        // HttpClient does not require explicit close in Java 11
    }

    // ---- Internal ----

    private Map<String, Object> post(String path, Map<String, Object> body) {
        String jsonBody = Json.serialize(body);
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(baseUrl + path))
                .header("Content-Type", "application/json")
                .header("Authorization", "Bearer " + token)
                .POST(HttpRequest.BodyPublishers.ofString(jsonBody))
                .timeout(Duration.ofSeconds(30))
                .build();

        HttpResponse<String> response;
        try {
            response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        } catch (Exception e) {
            throw new RuntimeException("HTTP request failed: " + e.getMessage(), e);
        }

        return handleResponse(response);
    }

    private Map<String, Object> handleResponse(HttpResponse<String> response) {
        String text = response.body();
        Map<String, Object> json;
        try {
            json = (text != null && !text.isEmpty()) ? Json.parse(text) : Map.of();
        } catch (Exception e) {
            throw new TinyHumansError(
                    "HTTP " + response.statusCode() + ": non-JSON response",
                    response.statusCode(),
                    text
            );
        }

        if (response.statusCode() < 200 || response.statusCode() >= 300) {
            String message = "HTTP " + response.statusCode();
            Object error = json.get("error");
            if (error instanceof String) {
                message = (String) error;
            }
            throw new TinyHumansError(message, response.statusCode(), json);
        }

        return json;
    }
}
