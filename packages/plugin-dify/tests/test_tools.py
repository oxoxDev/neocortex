"""Tests for Neocortex Dify tools."""

import pytest
from unittest.mock import MagicMock, patch

from neocortex_dify.tools.save_memory import SaveMemoryTool
from tinyhumansai import TinyHumanMemoryClient


class MockRuntime:
    def __init__(self, token):
        self.credentials = {"alphahuman_api_key": token, "default_namespace": "test_space"}

@patch("neocortex_dify.tools.save_memory.TinyHumanMemoryClient")
def test_save_memory_tool(mock_client_class):
    mock_instance = MagicMock()
    mock_client_class.return_value = mock_instance
    
    tool = SaveMemoryTool()
    tool.runtime = MockRuntime("fake_token")
    
    # We mock create_text_message because it's part of the Dify Tool base class which needs a real env
    tool.create_text_message = MagicMock(return_value={"text": "Success"})
    
    res = tool._invoke({
        "key": "test_key",
        "content": "test content",
        "namespace": "test_ns"
    })
    
    assert mock_client_class.called
    assert mock_instance.ingest_memory.called
    assert tool.create_text_message.called
