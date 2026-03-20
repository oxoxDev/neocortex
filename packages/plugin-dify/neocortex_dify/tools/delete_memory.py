from typing import Any

from dify_plugin import Tool

# We must import from tinyhumansai within the tool to run in the runner env
from tinyhumansai import TinyHumanMemoryClient, TinyHumanError


class DeleteMemoryTool(Tool):
    """
    Delete Memory Tool for Dify.
    """

    def _invoke(self, tool_parameters: dict[str, Any]) -> dict[str, Any]:
        """
        Tool implementation
        """
        namespace = tool_parameters.get('namespace')

        token = self.runtime.credentials.get('alphahuman_api_key')
        default_namespace = self.runtime.credentials.get('default_namespace') or "agent_memory"
        
        if not token:
            return self.create_text_message("Error: missing alphahuman_api_key credential.")

        client = TinyHumanMemoryClient(token=token)
        ns = namespace or default_namespace

        try:
            client.delete_memory(namespace=ns, delete_all=True)
            return self.create_text_message(f"Deleted memories from namespace '{ns}'.")
        except TinyHumanError as exc:
            return self.create_text_message(f"Failed to delete memory: {exc}")
