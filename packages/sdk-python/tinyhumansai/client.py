"""TinyHumans memory client for Python."""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Optional, Sequence, Union

import httpx

from .llm import recall_with_llm as _query_llm_func
from .types import (
    BASE_URL_ENV,
    TinyHumanError,
    DEFAULT_BASE_URL,
    DeleteMemoryResponse,
    GetContextResponse,
    IngestMemoryResponse,
    LLMQueryResponse,
    MemoryItem,
    ReadMemoryItem,
)


logger = logging.getLogger("tinyhumansai")

INSERT_PATH = "/v1/memory/insert"
QUERY_PATH = "/v1/memory/query"
DELETE_PATH = "/v1/memory/admin/delete"


def _validate_timestamp(value: Optional[float], name: str) -> None:
    """Validate a Unix timestamp (seconds).

    Args:
        value: Timestamp to validate (None is allowed).
        name: Field name for error messages.

    Raises:
        ValueError: If timestamp is invalid.
    """
    if value is None:
        return
    if not isinstance(value, (int, float)):
        raise ValueError(
            f"{name} must be a number (Unix timestamp in seconds), got {type(value).__name__}"
        )
    if value < 0:
        raise ValueError(
            f"{name} must be non-negative (Unix timestamp in seconds), got {value}"
        )
    # Reject timestamps that are too far in the future (e.g., > 100 years from now)
    max_future = time.time() + (100 * 365 * 24 * 60 * 60)
    if value > max_future:
        raise ValueError(
            f"{name} is too far in the future (max ~100 years), got {value}"
        )


def _validate_timestamps(
    created_at: Optional[float], updated_at: Optional[float]
) -> None:
    """Validate created_at and updated_at timestamps together.

    Args:
        created_at: Creation timestamp (None is allowed).
        updated_at: Update timestamp (None is allowed).

    Raises:
        ValueError: If timestamps are invalid or inconsistent.
    """
    _validate_timestamp(created_at, "created_at")
    _validate_timestamp(updated_at, "updated_at")
    if created_at is not None and updated_at is not None:
        if updated_at < created_at:
            raise ValueError(
                f"updated_at ({updated_at}) must be >= created_at ({created_at})"
            )


class TinyHumanMemoryClient:
    """Synchronous client for the TinyHumans memory API.

    Args:
        token: API token.
        model_id: Model identifier sent with every request. Defaults to "neocortex-mk1".
        base_url: Optional API base URL override.
    """

    def __init__(
        self,
        token: str,
        model_id: str = "neocortex-mk1",
        base_url: Optional[str] = None,
    ) -> None:
        if not token or not token.strip():
            raise ValueError("token is required")
        if not model_id or not model_id.strip():
            raise ValueError("model_id is required")
        resolved_base_url = (
            base_url or os.environ.get(BASE_URL_ENV) or DEFAULT_BASE_URL
        )
        self._base_url = resolved_base_url.rstrip("/")
        self._token = token
        self._model_id = model_id
        logger.debug(
            "Initializing TinyHumanMemoryClient base_url=%s model_id=%s",
            self._base_url,
            self._model_id,
        )
        self._http = httpx.Client(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {self._token}",
                "X-Model-Id": self._model_id,
            },
            timeout=30,
        )

    def close(self) -> None:
        """Close the underlying HTTP client and release connections."""
        logger.debug("Closing TinyHumanMemoryClient HTTP session")
        self._http.close()

    def __enter__(self) -> "TinyHumanMemoryClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def ingest_memory(
        self,
        *,
        item: Union[MemoryItem, dict[str, Any]],
    ) -> IngestMemoryResponse:
        """Ingest (upsert) a single memory item.

        The item is deduped by (namespace, key). If a matching item already
        exists its content and metadata are updated; otherwise a new item is created.

        Args:
            item: A `MemoryItem` or a dict with keys: `key` (str), `content` (str),
                `namespace` (str, required), optional `metadata` (dict),
                optional `created_at` (float, Unix seconds), optional `updated_at` (float, Unix seconds).

        Returns:
            Counts of ingested, updated, and errored items (ingested + updated <= 1).

        Raises:
            TinyHumanError: On API errors.
        """
        return self.ingest_memories(items=[item])

    def ingest_memories(
        self,
        *,
        items: Sequence[Union[MemoryItem, dict[str, Any]]],
    ) -> IngestMemoryResponse:
        """Ingest (upsert) one or more memory items.

        Items are deduped by (namespace, key). If a matching item already
        exists its content and metadata are updated; otherwise a new item
        is created.

        Args:
            items: Items to upsert. Each item can be a `MemoryItem` or a dict with
                keys: `key` (str), `content` (str), `namespace` (str, required),
                optional `metadata` (dict), optional `created_at` (float, Unix seconds),
                optional `updated_at` (float, Unix seconds).

        Returns:
            Counts of ingested, updated, and errored items.

        Raises:
            ValueError: If items list is empty.
            TinyHumanError: On API errors.
        """
        if not items:
            raise ValueError("items must be a non-empty list")

        normalized: list[dict[str, Any]] = []
        logger.debug("Normalizing %d memory item(s) for ingest", len(items))
        for item in items:
            if isinstance(item, MemoryItem):
                _validate_timestamps(item.created_at, item.updated_at)
                item_dict: dict[str, Any] = {
                    "key": item.key,
                    "content": item.content,
                    "namespace": item.namespace,
                    "metadata": item.metadata,
                }
                if item.created_at is not None:
                    item_dict["createdAt"] = item.created_at
                if item.updated_at is not None:
                    item_dict["updatedAt"] = item.updated_at
                normalized.append(item_dict)
            elif isinstance(item, dict):
                created_at = item.get("createdAt") or item.get("created_at")
                updated_at = item.get("updatedAt") or item.get("updated_at")
                _validate_timestamps(created_at, updated_at)
                if "namespace" not in item:
                    raise ValueError("items: each dict must include 'namespace'")
                item_dict = {
                    "key": item["key"],
                    "content": item["content"],
                    "namespace": item["namespace"],
                    "metadata": item.get("metadata", {}),
                }
                if created_at is not None:
                    item_dict["createdAt"] = created_at
                if updated_at is not None:
                    item_dict["updatedAt"] = updated_at
                normalized.append(item_dict)
            else:
                raise TypeError("items must be MemoryItem or dict")
        ingested = 0
        updated = 0
        for item_dict in normalized:
            body = self._build_insert_body(item_dict)
            logger.debug(
                "Sending ingest request namespace=%s key=%s",
                item_dict["namespace"],
                item_dict["key"],
            )
            data = self._send("POST", INSERT_PATH, body)
            status = str(data.get("status", "")).lower()
            if "updat" in status:
                updated += 1
            else:
                ingested += 1
        return IngestMemoryResponse(ingested=ingested, updated=updated, errors=0)

    def recall_memory(
        self,
        *,
        namespace: str,
        prompt: str,
        num_chunks: int = 10,
        key: Optional[str] = None,
        keys: Optional[Sequence[str]] = None,
    ) -> GetContextResponse:
        """Get an LLM-friendly context string from stored memory.

        Uses the given prompt to fetch relevant memory chunks from the namespace,
        then formats them into a single context string for use in an LLM prompt.

        Args:
            namespace: Namespace scope (required).
            prompt: Query used to retrieve relevant chunks (required).
            num_chunks: Maximum number of chunks to retrieve (default 10).
            key: Optional single key to include (bypasses prompt-based retrieval).
            keys: Optional list of keys to include (bypasses prompt-based retrieval).

        Returns:
            Context string and the source memory items.

        Raises:
            ValueError: If num_chunks is not positive.
            TinyHumanError: On API errors.
        """
        if num_chunks < 1:
            raise ValueError("num_chunks must be >= 1")
        logger.debug(
            "Recalling memory namespace=%s prompt=%s num_chunks=%d key=%s keys_count=%s",
            namespace,
            (prompt[:100] + "…") if len(prompt) > 100 else prompt,
            num_chunks,
            key,
            len(keys) if keys else 0,
        )
        body: dict[str, Any] = {
            "query": prompt,
            "namespace": namespace,
            "maxChunks": num_chunks,
        }
        if key:
            body["documentIds"] = [key]
        elif keys:
            body["documentIds"] = list(keys)

        data = self._send("POST", QUERY_PATH, body)
        items = self._extract_read_items(data, namespace)
        context = self._extract_context_string(data, items)
        return GetContextResponse(context=context, items=items, count=len(items))

    def delete_memory(
        self,
        *,
        namespace: str,
        key: Optional[str] = None,
        keys: Optional[Sequence[str]] = None,
        delete_all: bool = False,
    ) -> DeleteMemoryResponse:
        """Delete memory items by key, keys, or delete all.

        Args:
            namespace: Namespace scope (required).
            key: Optional single key to delete.
            keys: Optional array of keys to delete.
            delete_all: If true, delete all memory in this namespace.

        Returns:
            Count of deleted items.

        Raises:
            ValueError: If no deletion target is specified.
            TinyHumanError: On API errors.
        """
        has_key = isinstance(key, str) and len(key) > 0
        has_keys = isinstance(keys, (list, tuple)) and len(keys) > 0
        if has_key or has_keys:
            raise ValueError(
                "The current TinyHumans API only supports namespace-wide deletion. "
                "Pass delete_all=True to delete the namespace."
            )
        if not delete_all:
            raise ValueError('Set delete_all=True to confirm namespace deletion')

        body: dict[str, Any] = {"namespace": namespace}

        logger.debug(
            "Deleting memory namespace=%s key=%s keys_count=%s delete_all=%s",
            namespace,
            key,
            len(keys) if keys else 0,
            delete_all,
        )
        data = self._send("POST", DELETE_PATH, body)
        return DeleteMemoryResponse(deleted=int(data.get("nodesDeleted", 0)))

    def recall_with_llm(
        self,
        *,
        prompt: str,
        provider: str = "openai",
        model: str = "gpt-4o-mini",
        api_key: str,
        context: str = "",
        namespace: Optional[str] = None,
        num_chunks: int = 10,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        url: Optional[str] = None,
    ) -> LLMQueryResponse:
        """Optional: run a prompt through a supported LLM with optional context.

        If context is not provided, calls recall_memory(namespace=..., prompt=prompt, num_chunks=...)
        to fetch relevant chunks from memory. In that case namespace (and optionally num_chunks)
        must be provided.

        Uses the provider's REST API (no extra SDK deps). Requires a separate
        API key from the LLM provider.

        Supported built-in providers: ``openai``, ``anthropic``, ``google`` (Gemini).
        For custom providers, pass ``url`` to use an OpenAI-compatible API endpoint.

        Args:
            prompt: User prompt to send.
            provider: Provider name. For built-in: "openai", "anthropic", "google".
                For custom: any name (ignored if url is provided).
            model: Model name (e.g. "gpt-4o-mini", "claude-3-5-sonnet-20241022", "gemini-1.5-flash").
            api_key: Provider API key (not the TinyHumans token).
            context: Optional context string. If not provided and namespace is given,
                context is fetched via recall_memory(namespace=namespace, prompt=prompt, num_chunks=num_chunks).
            namespace: Optional namespace; used to fetch context when context is not provided.
            num_chunks: Number of chunks to fetch when context is auto-fetched (default 10).
            max_tokens: Optional max tokens to generate.
            temperature: Optional sampling temperature.
            url: Optional custom API endpoint URL. If provided, uses OpenAI-compatible format
                (POST with JSON body: {"model": ..., "messages": [{"role": "system/user", "content": ...}]}).
                Response expected: {"choices": [{"message": {"content": "..."}}]}.

        Returns:
            LLMQueryResponse with the model reply text.

        Raises:
            ValueError: If context is not provided and namespace is not provided; or provider/api_key invalid.
            TinyHumanError: On provider API errors.
        """
        if not context.strip():
            if not namespace:
                raise ValueError(
                    "When context is not provided, pass namespace (and optionally num_chunks) "
                    "so context can be fetched from memory via recall_memory."
                )
            ctx = self.recall_memory(
                namespace=namespace,
                prompt=prompt,
                num_chunks=num_chunks,
            )
            context = ctx.context
        logger.debug(
            "Calling recall_with_llm provider=%s model=%s namespace=%s "
            "has_context=%s max_tokens=%s temperature=%s url=%s",
            provider,
            model,
            namespace,
            bool(context),
            max_tokens,
            temperature,
            url,
        )
        return _query_llm_func(
            prompt=prompt,
            provider=provider,
            model=model,
            api_key=api_key,
            context=context,
            max_tokens=max_tokens,
            temperature=temperature,
            url=url,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _send(self, method: str, path: str, body: dict[str, Any]) -> dict[str, Any]:
        request = self._http.build_request(method, path, json=body)
        logger.debug(
            "HTTP %s %s headers=%s json=%s",
            method,
            request.url,
            self._debug_headers(),
            body,
        )
        response = self._http.send(request)
        return self._parse_response(response)

    def _build_insert_body(self, item: dict[str, Any]) -> dict[str, Any]:
        body: dict[str, Any] = {
            "title": item["key"],
            "content": item["content"],
            "namespace": item["namespace"],
            "documentId": item["key"],
        }
        if item.get("metadata"):
            body["metadata"] = item["metadata"]
        if item.get("createdAt") is not None:
            body["createdAt"] = item["createdAt"]
        if item.get("updatedAt") is not None:
            body["updatedAt"] = item["updatedAt"]
        return body

    def _extract_read_items(
        self, data: dict[str, Any], namespace: str
    ) -> list[ReadMemoryItem]:
        context = data.get("context")
        if not isinstance(context, dict):
            return []

        chunks = context.get("chunks")
        if not isinstance(chunks, list):
            return []

        items: list[ReadMemoryItem] = []
        for chunk in chunks:
            if not isinstance(chunk, dict):
                continue
            content = self._first_str(
                chunk,
                "content",
                "text",
                "chunkText",
                "body",
            )
            key = self._first_str(
                chunk,
                "documentId",
                "title",
                "id",
                default="",
            )
            item_namespace = self._first_str(
                chunk,
                "namespace",
                default=namespace,
            )
            metadata = {
                k: v
                for k, v in chunk.items()
                if k
                not in {
                    "content",
                    "text",
                    "chunkText",
                    "body",
                    "documentId",
                    "title",
                    "id",
                    "namespace",
                    "createdAt",
                    "updatedAt",
                }
            }
            items.append(
                ReadMemoryItem(
                    key=key,
                    content=content,
                    namespace=item_namespace,
                    metadata=metadata,
                    created_at=str(chunk.get("createdAt", "")),
                    updated_at=str(chunk.get("updatedAt", "")),
                )
            )
        return items

    def _extract_context_string(
        self, data: dict[str, Any], items: Sequence[ReadMemoryItem]
    ) -> str:
        llm_context = data.get("llmContextMessage")
        if isinstance(llm_context, str) and llm_context.strip():
            return llm_context

        context_parts: list[str] = []
        for item in items:
            header = f"[{item.namespace}:{item.key}]" if item.key else f"[{item.namespace}]"
            if item.content:
                context_parts.append(f"{header}\n{item.content}")
        return "\n\n".join(context_parts)

    def _debug_headers(self) -> dict[str, str]:
        return {
            "Authorization": "Bearer ***",
            "X-Model-Id": self._model_id,
            "Content-Type": "application/json",
        }

    def _first_str(
        self, payload: dict[str, Any], *keys: str, default: str = ""
    ) -> str:
        for key in keys:
            value = payload.get(key)
            if isinstance(value, str) and value:
                return value
        return default

    def _parse_response(self, response: httpx.Response) -> dict[str, Any]:
        response_text = response.text
        logger.debug(
            "HTTP response status=%s url=%s body=%s",
            response.status_code,
            response.url,
            response_text[:500].replace("\n", " "),
        )
        try:
            payload = response.json()
        except Exception:
            raise TinyHumanError(
                f"HTTP {response.status_code} {response.request.method} {response.url}: non-JSON response",
                response.status_code,
                response_text,
            )
        if not response.is_success:
            message = payload.get("error", f"HTTP {response.status_code}")
            raise TinyHumanError(message, response.status_code, payload)
        return payload["data"]
