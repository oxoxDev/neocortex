package xyz.tinyhumans.sdk;

public class WaitForIngestionJobOptions {

    private double timeoutSeconds = 30.0;
    private double pollIntervalSeconds = 1.0;

    public WaitForIngestionJobOptions() {}

    public WaitForIngestionJobOptions setTimeoutSeconds(double timeoutSeconds) { this.timeoutSeconds = timeoutSeconds; return this; }
    public WaitForIngestionJobOptions setPollIntervalSeconds(double pollIntervalSeconds) { this.pollIntervalSeconds = pollIntervalSeconds; return this; }

    public double getTimeoutSeconds() { return timeoutSeconds; }
    public double getPollIntervalSeconds() { return pollIntervalSeconds; }
}
