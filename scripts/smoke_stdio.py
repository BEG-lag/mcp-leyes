"""Start an mcp-leyes command over stdio and check the MCP handshake.

    uv run python scripts/smoke_stdio.py                      # python -m mcp_leyes.server
    uv run python scripts/smoke_stdio.py --query -- docker run -i --rm --network none \
        ghcr.io/beg-lag/mcp-leyes:1.0.0

CI and the release workflow use it to prove that a built container starts, speaks MCP over
stdio, reports the same version as this checkout and exposes every tool and prompt. With
--query it also reads article 27 of the Constitution, which proves that the data snapshot
inside the image answers without network.
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

from mcp_leyes import __version__

EXPECTED_TOOLS = {
    "list_laws",
    "get_article",
    "article_history",
    "diff_article",
    "diff_reform",
    "search",
    "reforms",
    "transitorios",
}
EXPECTED_PROMPTS = {"explain_reform", "trace_article"}


async def check(command: list[str], query: bool) -> list[str]:
    transport = StdioTransport(command=command[0], args=command[1:])
    problems = []
    async with Client(transport, timeout=120) as client:
        info = client.server_info
        tools = {tool.name for tool in await client.list_tools()}
        prompts = {prompt.name for prompt in await client.list_prompts()}
        if query:
            result = await client.call_tool(
                "get_article", {"law": "CPEUM", "article": "27"}, raise_on_error=False
            )
            text = result.content[0].text
            if result.is_error or "Corresponde a la Nación" not in text:
                problems.append(f"get_article(CPEUM, 27) failed: {text[:300]}")
            else:
                print(text.splitlines()[0], "...", sep="\n")
    if info.name != "leyes":
        problems.append(f"server name is {info.name!r}, expected 'leyes'")
    if info.version != __version__:
        problems.append(f"server version is {info.version!r}, expected {__version__!r}")
    if missing := EXPECTED_TOOLS - tools:
        problems.append(f"missing tools: {', '.join(sorted(missing))}")
    if missing := EXPECTED_PROMPTS - prompts:
        problems.append(f"missing prompts: {', '.join(sorted(missing))}")
    print(f"{info.name} {info.version}: {len(tools)} tools ({', '.join(sorted(tools))})")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--query", action="store_true", help="also call get_article(CPEUM, 27)")
    parser.add_argument("command", nargs="*", help="Command that starts the server over stdio.")
    args = parser.parse_args()
    command = args.command or [sys.executable, "-m", "mcp_leyes.server"]
    problems = asyncio.run(check(command, args.query))
    for problem in problems:
        print(f"FAIL: {problem}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
