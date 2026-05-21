"""Phase B — agent module imports and tool wiring."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def test_root_agent_exists():
    from agent.sales_analytics_agent.agent import root_agent

    assert root_agent.name == "jaybel_sales_analytics_agent"
    assert len(root_agent.tools) >= 1


def test_query_sales_analytics_tool_mocked():
    from agent.sales_analytics_agent import agent as agent_mod
    from pipeline.events import done, sql_event, status

    mock_result = MagicMock()
    mock_result.query_id = "q1"
    mock_result.l1 = None
    mock_result.sql = "SELECT 1"
    mock_result.query_result = None
    mock_result.answer = None
    mock_result.events = [status("ok"), sql_event("SELECT 1"), done("s", "q1")]

    with patch.object(agent_mod, "_get_pipeline") as gp:
        gp.return_value.run.return_value = mock_result
        out = agent_mod.query_sales_analytics("test question")

    assert out.startswith(agent_mod.SALES_PAYLOAD_PREFIX)
    payload = json.loads(out[len(agent_mod.SALES_PAYLOAD_PREFIX) :])
    assert payload["sql"] == "SELECT 1"
