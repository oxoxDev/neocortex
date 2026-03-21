# TinyHumans.Sdk (C#)

C# SDK for TinyHumans/TinyHuman Neocortex memory APIs.

## Requirements

- .NET 8 SDK

## Build

```bash
cd packages/sdk-csharp
dotnet build
```

## Get an API key

1. Sign in to your TinyHumans account.
2. Create a server API key in the TinyHumans dashboard.
3. Export it before running examples:

```bash
export TINYHUMANS_TOKEN="your_api_key"
# optional custom API URL
export TINYHUMANS_BASE_URL="https://api.tinyhumans.ai"
```

## Example (all SDK methods)

`example/TinyHumans.Sdk.Example/Program.cs` exercises every method exposed by this SDK:
- `InsertMemoryAsync`
- `RecallMemoryAsync`
- `QueryMemoryAsync`
- `RecallMemoriesAsync`
- `DeleteMemoryAsync`

Run it:

```bash
cd packages/sdk-csharp
dotnet run --project example/TinyHumans.Sdk.Example
```

## API scope

This SDK currently exposes the core memory routes only (insert/query/recall/recallMemories/delete).
