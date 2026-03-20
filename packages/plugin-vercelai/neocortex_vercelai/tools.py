"""Neocortex memory tools providing @tool decorated functions for Vercel AI SDK."""

import json
from typing import Optional, Dict

# The Vercel AI SDK uses ai_sdk in Python
from ai_sdk import tool
from tinyhumansai import TinyHumanMemoryClient, MemoryItem, TinyHumanError


class NeocortexMemoryTools:
    """Wrapper class providing Vercel AI SDK decorated tools for memory operations."""

    def __init__(self, client: TinyHumanMemoryClient, default_namespace: str = "agent_memory") -> None:
        """Initialize the tools wrapper.

        Args:
            client (TinyHumanMemoryClient): Configured Neocortex memory client.
            default_namespace (str): Fallback namespace if none is provided in calls.
        """
        self._client = client
        self._default_namespace = default_namespace

    def get_tools(self) -> Dict:
        """Return a dictionary of configured tools ready for generate_text/stream_text."""
        
        @tool(description="Save or update a single memory in Neocortex. Use this when you learn a fact (e.g. user preference, context) that should persist.")
        def save_memory(
            key: str,
            content: str,
            namespace: Optional[str] = None,
            metadata_json: Optional[str] = None,
        ) -> str:
            ns = namespace or self._default_namespace
            metadata: Dict = {}
            if metadata_json:
                try:
                    metadata = json.loads(metadata_json)
                except json.JSONDecodeError:
                    pass

            try:
                self._client.ingest_memory(
                    item=MemoryItem(
                        key=key,
                        content=content,
                        namespace=ns,
                        metadata=metadata,
                    )
                )
                return f"Saved memory '{key}' in namespace '{ns}'."
            except TinyHumanError as exc:
                return f"Failed to save memory: {exc}"

        @tool(description="Recall relevant memories from Neocortex for a given question or topic. Use this to look up past facts before answering.")
        def recall_memory(
            prompt: str,
            namespace: Optional[str] = None,
            num_chunks: int = 10,
        ) -> str:
            ns = namespace or self._default_namespace
            try:
                resp = self._client.recall_memory(
                    namespace=ns,
                    prompt=prompt,
                    num_chunks=num_chunks,
                )

                if not resp.items:
                    return f"No memories found in namespace '{ns}' for that query."

                texts = [item.content for item in resp.items if item.content.strip()]
                return "\\n\\n".join(texts)
            except TinyHumanError as exc:
                return f"Failed to recall memory: {exc}"

        @tool(description="Delete all memories in a given namespace from Neocortex.")
        def delete_memory(namespace: Optional[str] = None) -> str:
            ns = namespace or self._default_namespace
            try:
                self._client.delete_memory(namespace=ns, delete_all=True)
                return f"Deleted memories from namespace '{ns}'."
            except TinyHumanError as exc:
                return f"Failed to delete memory: {exc}"

        return {
            "save_memory": save_memory,
            "recall_memory": recall_memory,
            "delete_memory": delete_memory,
        }
