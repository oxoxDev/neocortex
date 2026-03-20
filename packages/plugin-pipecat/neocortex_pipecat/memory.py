from __future__ import annotations

from typing import Any, Dict, List, Optional
import os

import requests
from loguru import logger
from pydantic import BaseModel, Field

from pipecat.frames.frames import Frame, LLMContextFrame, LLMMessagesFrame
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.openai_llm_context import (
    OpenAILLMContext,
    OpenAILLMContextFrame,
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor


class NeocortexParams(BaseModel):
  """
  Configuration parameters for Neocortex memory service.

  Parameters:
      search_limit: Maximum number of memory chunks to retrieve per query.
      system_prompt: Prefix text for memory context messages.
      add_as_system_message: Whether to add memories as system messages.
      position: Position to insert memory messages in context (reserved for future use).
  """

  search_limit: int = Field(default=10, ge=1)
  system_prompt: str = Field(default="Based on previous conversations, I recall:\n\n")
  add_as_system_message: bool = Field(default=True)
  position: int = Field(default=1)


class NeocortexMemoryService(FrameProcessor):
  """
  A standalone memory service that integrates with Neocortex.

  This service intercepts message frames in the pipeline, stores user messages in
  Neocortex, and enhances context with relevant memories before passing them downstream.
  """

  def __init__(
    self,
    *,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    user_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    run_id: Optional[str] = None,
    params: Optional[NeocortexParams] = None,
  ) -> None:
    super().__init__()

    token = (api_key or os.getenv("ALPHAHUMAN_API_KEY") or "").strip()
    if not token:
      logger.error("NeocortexMemoryService: missing Neocortex API key (ALPHAHUMAN_API_KEY).")
      raise ValueError("Neocortex API key is required.")

    self._token = token
    self._base_url = (base_url or os.getenv("ALPHAHUMAN_BASE_URL") or "https://staging-api.alphahuman.xyz").rstrip("/")

    if not any([user_id, agent_id, run_id]):
      raise ValueError("At least one of user_id, agent_id, or run_id must be provided")

    self.user_id = user_id
    self.agent_id = agent_id
    self.run_id = run_id

    cfg = params or NeocortexParams()
    self.search_limit = cfg.search_limit
    self.system_prompt = cfg.system_prompt
    self.add_as_system_message = cfg.add_as_system_message
    self.position = cfg.position

    self._last_query: Optional[str] = None

    logger.info(
      "Initialized NeocortexMemoryService with "
      f"user_id={self.user_id}, agent_id={self.agent_id}, run_id={self.run_id}"
    )

  # ---------------------------
  # Low-level Neocortex client
  # ---------------------------

  def _headers(self) -> Dict[str, str]:
    return {
      "Authorization": f"Bearer {self._token}",
      "Content-Type": "application/json",
    }

  def _post(self, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{self._base_url}{path}"
    resp = requests.post(url, json=body, headers=self._headers(), timeout=30)
    try:
      data = resp.json() if resp.text else {}
    except Exception:
      resp.raise_for_status()
      return {}

    if not resp.ok or data.get("success") is False:
      msg = data.get("error") or f"HTTP {resp.status_code}"
      logger.error(f"Neocortex API error: {msg}")
      raise RuntimeError(msg)

    return data

  def _insert_memory(self, title: str, content: str, namespace: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    body: Dict[str, Any] = {
      "title": title,
      "content": content,
      "namespace": namespace,
      "sourceType": "chat",
      "metadata": metadata or {},
    }
    return self._post("/v1/memory/insert", body)

  def _query_memory(self, query: str, namespace: str, max_chunks: int) -> Dict[str, Any]:
    body: Dict[str, Any] = {
      "query": query,
      "namespace": namespace,
      "maxChunks": max_chunks,
    }
    return self._post("/v1/memory/query", body)

  def _delete_memory(self, namespace: Optional[str]) -> Dict[str, Any]:
    body: Dict[str, Any] = {
      "namespace": namespace,
    }
    return self._post("/v1/memory/admin/delete", body)

  # ---------------------------
  # Memory helpers
  # ---------------------------

  def _namespace_for(self) -> str:
    # Simple strategy: prefer run_id, then user_id, then agent_id, otherwise "default"
    if self.run_id:
      return f"pipecat-run-{self.run_id}"
    if self.user_id:
      return f"pipecat-user-{self.user_id}"
    if self.agent_id:
      return f"pipecat-agent-{self.agent_id}"
    return "pipecat-default"

  def _store_messages(self, messages: List[Dict[str, Any]]) -> None:
    """
    Store the latest user message as a Neocortex memory.
    """
    try:
      latest_user: Optional[Dict[str, Any]] = None
      for message in reversed(messages):
        if message.get("role") == "user" and isinstance(message.get("content"), str):
          latest_user = message
          break

      if not latest_user:
        return

      text = str(latest_user.get("content", "")).strip()
      if not text:
        return

      title = text[:64] + ("..." if len(text) > 64 else "")
      namespace = self._namespace_for()

      metadata: Dict[str, Any] = {
        "platform": "pipecat",
        "user_id": self.user_id,
        "agent_id": self.agent_id,
        "run_id": self.run_id,
      }

      logger.debug(f"NeocortexMemoryService: inserting memory in namespace={namespace}")
      self._insert_memory(title=title, content=text, namespace=namespace, metadata=metadata)
    except Exception as e:
      logger.error(f"Error storing messages in Neocortex: {e}")

  def _retrieve_memories(self, query: str) -> str:
    """
    Retrieve relevant memories from Neocortex and format them as a context string.
    """
    try:
      namespace = self._namespace_for()
      logger.debug(f"NeocortexMemoryService: querying memories for namespace={namespace}")
      res = self._query_memory(query=query, namespace=namespace, max_chunks=self.search_limit)
      data = res.get("data") or {}

      direct = data.get("llmContextMessage") or data.get("response")
      if isinstance(direct, str) and direct.strip():
        return direct.strip()

      chunks = ((data.get("context") or {}).get("chunks")) or []
      texts: List[str] = []
      for chunk in chunks:
        if isinstance(chunk, dict):
          text = chunk.get("content") or chunk.get("text") or chunk.get("body") or ""
          if isinstance(text, str) and text.strip():
            texts.append(text.strip())

      return "\n\n".join(texts)
    except Exception as e:
      logger.error(f"Error retrieving memories from Neocortex: {e}")
      return ""

  def _enhance_context_with_memories(self, context: LLMContext | OpenAILLMContext, query: str) -> None:
    """
    Enhance the LLM context with relevant memories.
    """
    if self._last_query == query:
      return

    self._last_query = query

    memory_text = self._retrieve_memories(query)
    if not memory_text:
      return

    full_text = f"{self.system_prompt}\n{memory_text}".strip()

    if not full_text:
      return

    if self.add_as_system_message:
      context.add_message({"role": "system", "content": full_text})
    else:
      context.add_message({"role": "user", "content": full_text})

    logger.debug("NeocortexMemoryService: enhanced context with Neocortex memories")

  # ---------------------------
  # FrameProcessor implementation
  # ---------------------------

  async def process_frame(self, frame: Frame, direction: FrameDirection):  # type: ignore[override]
    """
    Process incoming frames, intercept context frames for memory integration.
    """
    await super().process_frame(frame, direction)

    context: Optional[LLMContext | OpenAILLMContext] = None
    messages: Optional[List[Dict[str, Any]]] = None

    if isinstance(frame, (LLMContextFrame, OpenAILLMContextFrame)):
      context = frame.context
    elif isinstance(frame, LLMMessagesFrame):
      messages = frame.messages
      context = LLMContext(messages)

    if context:
      try:
        context_messages = context.get_messages()
        latest_user_message = None

        for message in reversed(context_messages):
          if message.get("role") == "user" and isinstance(message.get("content"), str):
            latest_user_message = message.get("content")
            break

        if isinstance(latest_user_message, str) and latest_user_message.strip():
          # Enhance context and then store messages
          self._enhance_context_with_memories(context, latest_user_message)
          self._store_messages(context_messages)

        if messages is not None:
          # Re-emit messages with enhanced context
          await self.push_frame(LLMMessagesFrame(context.get_messages()))
        else:
          await self.push_frame(frame)
      except Exception as e:
        await self.push_error(
          error_msg=f"Error processing with NeocortexMemoryService: {str(e)}", exception=e
        )
        await self.push_frame(frame)
    else:
      await self.push_frame(frame, direction)

