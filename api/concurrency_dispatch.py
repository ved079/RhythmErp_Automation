"""Dispatch concurrent test runs to multiple PC agents and merge SSE streams."""

import asyncio
import json
import os
import time
from typing import AsyncGenerator

import httpx

from api.models import ConcurrencyDispatchRequest, AgentStatusResponse


def _resolve_agent_urls(request: ConcurrencyDispatchRequest) -> list[str]:
    """Resolve agent URLs from the request or environment variable."""
    if request.agents:
        return [u.strip() for u in request.agents if u.strip()]
    env_urls = os.environ.get("PC_AGENT_URLS", "")
    if not env_urls:
        return []
    return [u.strip() for u in env_urls.split(",") if u.strip()]


async def dispatch_concurrent(request: ConcurrencyDispatchRequest) -> AsyncGenerator[str, None]:
    """Dispatch a test run to all PC agents and merge their SSE streams.

    Each agent event is tagged with a ``pc`` field (e.g. "PC-1", "PC-2").
    Streams are merged via an ``asyncio.Queue`` so events arrive in real time
    from whichever agent responds first.
    """
    agent_urls = _resolve_agent_urls(request)
    if not agent_urls:
        yield f"data: {json.dumps({'type': 'error', 'message': 'No PC agents configured. Set PC_AGENT_URLS or pass agents list.'})}\n\n"
        return

    secret = os.environ.get("AGENT_SECRET", "dev-secret")
    queue: asyncio.Queue[str | None] = asyncio.Queue()
    payload = request.payload.model_dump()

    async def _stream_from_agent(url: str, pc_name: str) -> None:
        """Connect to one agent and push its SSE events into the shared queue."""
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(300)) as client:
                async with client.stream(
                    "POST",
                    f"{url.rstrip('/')}/run",
                    json=payload,
                    headers={"x-secret": secret},
                ) as resp:
                    async for line in resp.aiter_lines():
                        if line.startswith("data: "):
                            try:
                                event = json.loads(line[6:])
                                event["pc"] = pc_name
                                await queue.put(f"data: {json.dumps(event)}\n\n")
                            except json.JSONDecodeError:
                                await queue.put(line + "\n\n")
        except Exception as exc:
            error_event = {
                "type": "error",
                "message": f"Agent {pc_name} ({url}) failed: {exc}",
                "pc": pc_name,
            }
            await queue.put(f"data: {json.dumps(error_event)}\n\n")
        finally:
            await queue.put(None)

    tasks = [
        asyncio.create_task(_stream_from_agent(url, f"PC-{i + 1}"))
        for i, url in enumerate(agent_urls)
    ]

    completed = 0
    while completed < len(tasks):
        item = await queue.get()
        if item is None:
            completed += 1
        else:
            yield item


async def ping_agents() -> list[AgentStatusResponse]:
    """Ping all configured PC agents and return their health status."""
    agent_urls_str = os.environ.get("PC_AGENT_URLS", "")
    urls = [u.strip() for u in agent_urls_str.split(",") if u.strip()]
    if not urls:
        return []

    async def _ping(url: str, pc_name: str) -> AgentStatusResponse:
        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10)) as client:
                resp = await client.get(f"{url.rstrip('/')}/health")
                elapsed = (time.monotonic() - start) * 1000
                if resp.status_code == 200:
                    data = resp.json()
                    return AgentStatusResponse(
                        url=url,
                        pc=data.get("pc", pc_name),
                        status="ok",
                        latency_ms=round(elapsed, 1),
                    )
        except Exception:
            pass
        return AgentStatusResponse(
            url=url,
            pc=pc_name,
            status="unreachable",
            latency_ms=0,
        )

    tasks = [
        asyncio.create_task(_ping(url, f"PC-{i + 1}"))
        for i, url in enumerate(urls)
    ]
    return await asyncio.gather(*tasks)
