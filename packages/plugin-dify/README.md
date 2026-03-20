# plugin-dify

Neocortex (Alphahuman) memory tool extension for Dify AI.

## Features

Provides custom tools for Dify that can be integrated into your Apps and Workflows:
- **`save_memory`**: Save facts to Neocortex.
- **`recall_memory`**: Search Neocortex for context.
- **`delete_memory`**: Clear a memory namespace.

## Installation into Dify

This package is structured as a Dify Tool Plugin.

1. Install the [Dify Plugin CLI](https://github.com/langgenius/dify-plugin).
2. Follow the Dify documentation to package this plugin:
   ```bash
   dify plugin package neocortex_dify
   ```
3. Upload the resulting `.difypkg` file to your Dify instance via the "Plugins" page in the dashboard.
4. When configuring the plugin in Dify, provide your `alphahuman_api_key` and an optional `default_namespace`.

## Local Testing

To run the unit tests:
```bash
pip install -e .[dev]
pytest tests/
```
