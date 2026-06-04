import pytest
from unittest.mock import AsyncMock, patch
from backend.agents.engine import run_agent, run_parallel


@pytest.mark.asyncio
async def test_run_agent_returns_parsed_json():
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock()]
    mock_response.choices[0].message.content = '{"name": "Alice", "role": "protagonist"}'

    with patch("backend.agents.engine._make_openai_call", return_value=mock_response):
        result = await run_agent("Extract characters", {"text": "..."}, model="gpt-4o")

    assert result == {"name": "Alice", "role": "protagonist"}


@pytest.mark.asyncio
async def test_run_agent_retries_on_failure():
    call_count = 0

    async def mock_call(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise Exception("API error")
        mock = AsyncMock()
        mock.choices = [AsyncMock()]
        mock.choices[0].message.content = '{"status": "ok"}'
        return mock

    with patch("backend.agents.engine._make_openai_call", side_effect=mock_call):
        result = await run_agent("test", {}, max_retries=3)

    assert result == {"status": "ok"}
    assert call_count == 3


@pytest.mark.asyncio
async def test_run_parallel_dispatches_concurrently():
    async def mock_agent(text: str) -> dict:
        return {"text": text, "length": len(text)}

    items = [{"text": "hello"}, {"text": "world"}, {"text": "test"}]
    results = await run_parallel(mock_agent, items, concurrency=2)

    assert len(results) == 3
    assert results[0]["text"] == "hello"
