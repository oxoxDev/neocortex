# tinyhumans_sdk (Dart)

Dart SDK for TinyHumans/TinyHuman Neocortex memory APIs.

## Requirements

- Dart 3.0+

## Install

From pub:

```bash
dart pub add tinyhumans_sdk
```

Or from this repository:

```bash
cd packages/sdk-dart
dart pub get
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

`example/example.dart` exercises every method exposed by this SDK:
- `insertMemory`
- `recallMemory`
- `queryMemory`
- `recallMemories`
- `deleteMemory`

Run it:

```bash
cd packages/sdk-dart
dart run example/example.dart
```

## API scope

This SDK currently exposes the core memory routes only (insert/query/recall/recallMemories/delete).
