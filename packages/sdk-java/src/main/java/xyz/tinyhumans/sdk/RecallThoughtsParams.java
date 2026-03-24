package xyz.tinyhumans.sdk;

import java.util.LinkedHashMap;
import java.util.Map;

public class RecallThoughtsParams {

    private String namespace;
    private Integer maxChunks;
    private Double temperature;
    private Integer randomnessSeed;
    private Boolean persist;
    private Boolean enablePredictionCheck;
    private String thoughtPrompt;

    public RecallThoughtsParams() {}

    public Map<String, Object> toMap() {
        Map<String, Object> map = new LinkedHashMap<>();
        if (namespace != null) map.put("namespace", namespace);
        if (maxChunks != null) map.put("maxChunks", maxChunks);
        if (temperature != null) map.put("temperature", temperature);
        if (randomnessSeed != null) map.put("randomnessSeed", randomnessSeed);
        if (persist != null) map.put("persist", persist);
        if (enablePredictionCheck != null) map.put("enablePredictionCheck", enablePredictionCheck);
        if (thoughtPrompt != null) map.put("thoughtPrompt", thoughtPrompt);
        return map;
    }

    public RecallThoughtsParams setNamespace(String namespace) { this.namespace = namespace; return this; }
    public RecallThoughtsParams setMaxChunks(Integer maxChunks) { this.maxChunks = maxChunks; return this; }
    public RecallThoughtsParams setTemperature(Double temperature) { this.temperature = temperature; return this; }
    public RecallThoughtsParams setRandomnessSeed(Integer randomnessSeed) { this.randomnessSeed = randomnessSeed; return this; }
    public RecallThoughtsParams setPersist(Boolean persist) { this.persist = persist; return this; }
    public RecallThoughtsParams setEnablePredictionCheck(Boolean enablePredictionCheck) { this.enablePredictionCheck = enablePredictionCheck; return this; }
    public RecallThoughtsParams setThoughtPrompt(String thoughtPrompt) { this.thoughtPrompt = thoughtPrompt; return this; }

    public String getNamespace() { return namespace; }
    public Integer getMaxChunks() { return maxChunks; }
    public Double getTemperature() { return temperature; }
    public Integer getRandomnessSeed() { return randomnessSeed; }
    public Boolean getPersist() { return persist; }
    public Boolean getEnablePredictionCheck() { return enablePredictionCheck; }
    public String getThoughtPrompt() { return thoughtPrompt; }
}
