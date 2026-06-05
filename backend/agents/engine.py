from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Callable, Coroutine

from openai import AsyncOpenAI

from backend.config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL, AGENT_CONCURRENCY

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
    return _client


async def _make_openai_call(
    prompt: str,
    model: str = OPENAI_MODEL,
    temperature: float = 0.3,
    max_tokens: int = 4096,
) -> Any:
    client = _get_client()
    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
    )
    return response


async def run_agent(
    prompt: str,
    context: dict[str, Any] | None = None,
    model: str = OPENAI_MODEL,
    max_retries: int = 3,
) -> dict[str, Any]:
    """Run a single agent call to OpenAI and return parsed JSON result."""
    full_prompt = prompt
    if context:
        full_prompt = f"{prompt}\n\nInput data:\n{json.dumps(context, ensure_ascii=False)}"

    last_error = None
    for attempt in range(max_retries):
        try:
            response = await _make_openai_call(full_prompt, model=model)
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            last_error = e
            logger.warning(f"Agent call attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)

    raise RuntimeError(f"Agent call failed after {max_retries} attempts: {last_error}")


async def run_parallel(
    agent_func: Callable[..., Coroutine[Any, Any, dict]],
    items: list[dict[str, Any]],
    concurrency: int = AGENT_CONCURRENCY,
) -> list[dict[str, Any]]:
    """Run agent_func on each item in parallel, limited by concurrency semaphore."""
    semaphore = asyncio.Semaphore(concurrency)

    async def _run_with_limit(item: dict) -> dict:
        async with semaphore:
            return await agent_func(**item)

    tasks = [_run_with_limit(item) for item in items]
    return await asyncio.gather(*tasks)
