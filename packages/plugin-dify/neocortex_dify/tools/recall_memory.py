from typing import Any

from dify_plugin import Tool

# We must import from tinyhumansai within the tool to run in the runner env
from tinyhumansai import TinyHumanMemoryClient, TinyHumanError


class RecallMemoryTool(Tool):
    """
    Recall Memory Tool for Dify.
    """

    def _invoke(self, tool_parameters: dict[str, Any]) -> dict[str, Any]:
        """
        Tool implementation
        """
        prompt = tool_parameters.get('prompt')
        namespace = tool_parameters.get('namespace')
        num_chunks = tool_parameters.get('num_chunks') or 10

        token = self.runtime.credentials.get('alphahuman_api_key')
        default_namespace = self.runtime.credentials.get('default_namespace') or "agent_memory"
        
        if not token:
            return self.create_text_message("Error: missing alphahuman_api_key credential.")
        if not prompt:
            return self.create_text_message("Error: prompt is required.")

        client = TinyHumanMemoryClient(token=token)
        ns = namespace or default_namespace

        try:
            resp = client.recall_memory(
                namespace=ns,
                prompt=prompt,
                num_chunks=int(num_chunks),
            )

            if not resp.items:
                return self.create_text_message(f"No memories found in namespace '{ns}' for that query.")

            texts = [item.content for item in resp.items if item.content.strip()]
            return self.create_text_message("\\n\\n".join(texts))
        except TinyHumanError as exc:
            return self.create_text_message(f"Failed to recall memory: {exc}")
