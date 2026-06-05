from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any, Callable, Coroutine

from openai import AsyncOpenAI

from backend.config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL, AGENT_CONCURRENCY, OPENAI_AUTH_HEADER, OPENAI_CUSTOM_HEADERS

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        kwargs: dict[str, Any] = {"base_url": OPENAI_BASE_URL}
        headers: dict[str, str] = {}

        if OPENAI_CUSTOM_HEADERS:
            # 完全自定义 headers（JSON 格式，如 {"X-API-Key": "xxx"}）
            import json as _json
            headers.update(_json.loads(OPENAI_CUSTOM_HEADERS))

        if OPENAI_AUTH_HEADER:
            # 自定义 Authorization header value（覆盖可能存在的 Authorization）
            headers["Authorization"] = OPENAI_AUTH_HEADER
        elif "Authorization" not in headers:
            # 默认使用标准 Bearer 认证
            kwargs["api_key"] = OPENAI_API_KEY

        if headers:
            kwargs["default_headers"] = headers

        _client = AsyncOpenAI(**kwargs)
    return _client


def _parse_json_response(content: str) -> dict[str, Any]:
    """Parse LLM JSON response with recovery for truncation and markdown fences."""
    # Strip markdown code fences
    md_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", content, re.DOTALL)
    if md_match:
        content = md_match.group(1).strip()
    else:
        content = content.strip()

    # Try direct parse
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Repair truncated JSON: walk characters tracking structural state,
    # then close unclosed brackets and strings.
    in_string = False
    in_escape = False
    last_boundary = 0
    stack: list[str] = []

    for i, ch in enumerate(content):
        if in_escape:
            in_escape = False
            continue
        if ch == "\\" and in_string:
            in_escape = True
            continue
        if ch == '"' and not in_escape:
            in_string = not in_string
            last_boundary = i + 1
            continue
        if in_string:
            continue
        if ch in "{[":
            stack.append(ch)
        elif ch in "}]":
            expected = "{" if ch == "}" else "["
            if stack and stack[-1] == expected:
                stack.pop()
                if not stack:
                    last_boundary = i + 1
        elif ch == "," and not stack:
            last_boundary = i + 1

    # Build closing suffix
    brace_map = {"{": "}", "[": "]"}
    suffix = "".join(brace_map[b] for b in reversed(stack))

    # If cut off mid-string, close it
    if in_string:
        repair = content[:last_boundary] + '"' + suffix
    else:
        repair = content[:last_boundary] + suffix

    try:
        return json.loads(repair)
    except json.JSONDecodeError:
        # Last resort: try progressively shorter prefixes
        for i in range(len(repair) - 1, 0, -1):
            try:
                return json.loads(repair[:i] + suffix)
            except json.JSONDecodeError:
                continue

    raise json.JSONDecodeError("Failed to repair truncated JSON", content, 0)


async def _make_openai_call(
    prompt: str,
    model: str = OPENAI_MODEL,
    temperature: float = 0.3,
    max_completion_tokens: int = 4096,
) -> Any:
    client = _get_client()
    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_completion_tokens=max_completion_tokens,
        response_format={"type": "json_object"},
    )
    return response


async def run_agent(
    prompt: str,
    context: dict[str, Any] | None = None,
    model: str = OPENAI_MODEL,
    max_retries: int = 3,
    max_completion_tokens: int = 4096,
    max_completion_tokens_scale: int = 2,
) -> dict[str, Any]:
    """Run a single agent call to OpenAI and return parsed JSON result."""
    full_prompt = prompt
    if context:
        full_prompt = f"{prompt}\n\nInput data:\n{json.dumps(context, ensure_ascii=False)}"

    last_error = None
    for attempt in range(max_retries):
        try:
            response = await _make_openai_call(
                full_prompt,
                model=model,
                max_completion_tokens=max_completion_tokens,
            )
            content = response.choices[0].message.content
            return _parse_json_response(content)
        except json.JSONDecodeError as e:
            last_error = e
            logger.warning(
                f"Agent call attempt {attempt + 1}/{max_retries} failed (JSON error): {e}"
            )
            if attempt < max_retries - 1:
                max_completion_tokens *= max_completion_tokens_scale
                logger.info(
                    f"Retrying with max_completion_tokens={max_completion_tokens}"
                )
                await asyncio.sleep(2 ** attempt)
        except Exception as e:
            last_error = e
            logger.warning(
                f"Agent call attempt {attempt + 1}/{max_retries} failed: {e}"
            )
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
