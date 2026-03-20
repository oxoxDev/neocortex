"""Tests for Neocortex memory tools."""

import pytest
from unittest.mock import MagicMock

from neocortex_vercelai import NeocortexMemoryTools
from tinyhumansai import TinyHumanMemoryClient

@pytest.fixture
def mock_client():
    return MagicMock(spec=TinyHumanMemoryClient)

def test_get_tools(mock_client):
    wrapper = NeocortexMemoryTools(client=mock_client)
    tools = wrapper.get_tools()
    
    assert "save_memory" in tools
    assert "recall_memory" in tools
    assert "delete_memory" in tools

    # The tools are decorated with @tool, but the underlying function is still accessible / callable
    save_tool = tools["save_memory"]
    
    # Executing the function directly
    res = save_tool.execute(key="test", content="value", namespace="ns", metadata_json=None)
    assert mock_client.ingest_memory.called
    assert "test" in res
