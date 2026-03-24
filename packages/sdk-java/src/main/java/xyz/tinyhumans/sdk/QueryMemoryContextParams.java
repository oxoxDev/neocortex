package xyz.tinyhumans.sdk;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public class QueryMemoryContextParams {

    private String query;
    private String namespace;
    private Boolean includeReferences;
    private Integer maxChunks;
    private List<String> documentIds;
    private Boolean recallOnly;
    private String llmQuery;

    public QueryMemoryContextParams() {}

    public QueryMemoryContextParams(String query) {
        this.query = query;
    }

    public void validate() {
        if (query == null || query.isEmpty()) {
            throw new IllegalArgumentException("query is required and must be a non-empty string");
        }
    }

    public Map<String, Object> toMap() {
        validate();
        Map<String, Object> map = new LinkedHashMap<>();
        map.put("query", query);
        if (namespace != null) map.put("namespace", namespace);
        if (includeReferences != null) map.put("includeReferences", includeReferences);
        if (maxChunks != null) map.put("maxChunks", maxChunks);
        if (documentIds != null) map.put("documentIds", documentIds);
        if (recallOnly != null) map.put("recallOnly", recallOnly);
        if (llmQuery != null) map.put("llmQuery", llmQuery);
        return map;
    }

    public QueryMemoryContextParams setQuery(String query) { this.query = query; return this; }
    public QueryMemoryContextParams setNamespace(String namespace) { this.namespace = namespace; return this; }
    public QueryMemoryContextParams setIncludeReferences(Boolean includeReferences) { this.includeReferences = includeReferences; return this; }
    public QueryMemoryContextParams setMaxChunks(Integer maxChunks) { this.maxChunks = maxChunks; return this; }
    public QueryMemoryContextParams setDocumentIds(List<String> documentIds) { this.documentIds = documentIds; return this; }
    public QueryMemoryContextParams setRecallOnly(Boolean recallOnly) { this.recallOnly = recallOnly; return this; }
    public QueryMemoryContextParams setLlmQuery(String llmQuery) { this.llmQuery = llmQuery; return this; }

    public String getQuery() { return query; }
    public String getNamespace() { return namespace; }
    public Boolean getIncludeReferences() { return includeReferences; }
    public Integer getMaxChunks() { return maxChunks; }
    public List<String> getDocumentIds() { return documentIds; }
    public Boolean getRecallOnly() { return recallOnly; }
    public String getLlmQuery() { return llmQuery; }
}
