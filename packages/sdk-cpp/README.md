# tinyhumans-sdk-cpp

C++ SDK for TinyHumans/TinyHuman Neocortex memory APIs.

## Requirements

- C++17+
- CMake 3.14+
- libcurl

## Build

```bash
cd packages/sdk-cpp
make build
```

This builds the SDK library and the example binary.

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

`example/example_usage.cpp` exercises every method exposed by this SDK:
- `insert_memory`
- `recall_memory`
- `query_memory`
- `recall_memories`
- `delete_memory`

Run it:

```bash
cd packages/sdk-cpp
./build/example_usage
```

## API scope

This SDK currently exposes the core memory routes only (insert/query/recall/recall_memories/delete).
