import json
from typing import Any, Dict

from dify_plugin import Tool

# We must import from tinyhumansai within the tool to run in the runner env
from tinyhumansai import TinyHumanMemoryClient, MemoryItem, TinyHumanError


class SaveMemoryTool(Tool):
    """
    Save Memory Tool for Dify.
    """

    def _invoke(self, tool_parameters: dict[str, Any]) -> dict[str, Any]:
        """
        Tool implementation
        """
        key = tool_parameters.get('key')
        content = tool_parameters.get('content')
        namespace = tool_parameters.get('namespace')
        metadata_json = tool_parameters.get('metadata_json')
        
        token = self.runtime.credentials.get('alphahuman_api_key')
        default_namespace = self.runtime.credentials.get('default_namespace') or "agent_memory"
        
        if not token:
            return self.create_text_message("Error: missing alphahuman_api_key credential.")
        if not key or not content:
            return self.create_text_message("Error: key and content are required.")

        client = TinyHumanMemoryClient(token=token)
        ns = namespace or default_namespace

        metadata: Dict = {}
        if metadata_json:
            try:
                metadata = json.loads(metadata_json)
            except json.JSONDecodeError:
                pass

        try:
            client.ingest_memory(
                item=MemoryItem(
                    key=key,
                    content=content,
                    namespace=ns,
                    metadata=metadata,
                )
            )
            return self.create_text_message(f"Saved memory '{key}' in namespace '{ns}'.")
        except TinyHumanError as exc:
            return self.create_text_message(f"Failed to save memory: {exc}")
