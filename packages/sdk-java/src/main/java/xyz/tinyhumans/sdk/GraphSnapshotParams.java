package xyz.tinyhumans.sdk;

import java.util.LinkedHashMap;
import java.util.Map;

public class GraphSnapshotParams {

    private String namespace;
    private String mode;
    private Integer limit;
    private Integer seedLimit;

    public GraphSnapshotParams() {}

    public Map<String, String> toQueryParams() {
        Map<String, String> params = new LinkedHashMap<>();
        if (namespace != null) params.put("namespace", namespace);
        if (mode != null) params.put("mode", mode);
        if (limit != null) params.put("limit", String.valueOf(limit));
        if (seedLimit != null) params.put("seed_limit", String.valueOf(seedLimit));
        return params;
    }

    public GraphSnapshotParams setNamespace(String namespace) { this.namespace = namespace; return this; }
    public GraphSnapshotParams setMode(String mode) { this.mode = mode; return this; }
    public GraphSnapshotParams setLimit(Integer limit) { this.limit = limit; return this; }
    public GraphSnapshotParams setSeedLimit(Integer seedLimit) { this.seedLimit = seedLimit; return this; }

    public String getNamespace() { return namespace; }
    public String getMode() { return mode; }
    public Integer getLimit() { return limit; }
    public Integer getSeedLimit() { return seedLimit; }
}
