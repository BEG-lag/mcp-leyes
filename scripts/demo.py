"""Run the real server over stdio against the real leyes-mx and record a transcript.

    uv run python scripts/demo.py                  # prints the transcript
    uv run python scripts/demo.py --write          # also writes docs/demo.md
    MCP_LEYES_SOURCE=~/GitHub/leyes-mx uv run python scripts/demo.py   # from a local clone

It starts from an empty cache in a temporary directory, so the first call includes the
first sync (git clone of leyes-mx plus indexing) and its timing is real. Everything in
docs/demo.md is exactly what an MCP client such as Claude receives.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import tempfile
import time
from pathlib import Path

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

from mcp_leyes.config import DEFAULT_SOURCE
from mcp_leyes.dates import today_mx

DOCS = Path(__file__).resolve().parent.parent / "docs" / "demo.md"

CALLS: list[tuple[str, dict]] = [
    ("list_laws", {}),
    ("get_article", {"law": "CPEUM", "article": "27", "date": "2013-01-01"}),
    ("article_history", {"law": "CPEUM", "article": "27"}),
    ("diff_article", {"law": "CPEUM", "article": "27", "date_from": "2013-01-01"}),
    ("diff_reform", {"law": "LFT", "reform_date": "2019-05-01", "limit": 3}),
    (
        "diff_article",
        {"law": "LFT", "article": "371", "date_from": "2019-01-01", "date_to": "2019-12-31"},
    ),
    ("get_article", {"law": "LFT", "article": "371", "date": "2019-06-01"}),
    ("transitorios", {"law": "LFT", "decree_date": "2019-05-01", "max_chars": 4000}),
    ("search", {"query": 'subcontrat "servicios especializados"', "limit": 5}),
    ("reforms", {"law": "LFT", "since": "2019-01-01", "limit": 10}),
    ("get_article", {"law": "LISR", "article": "9"}),
    ("get_article", {"law": "CCom", "article": "291", "date": "2010-01-01"}),
]


async def run(cache: str) -> tuple[list[str], dict]:
    env = dict(os.environ)
    env["MCP_LEYES_CACHE"] = cache
    source = env.get("MCP_LEYES_SOURCE", DEFAULT_SOURCE)
    transport = StdioTransport(command=sys.executable, args=["-m", "mcp_leyes.server"], env=env)
    sections: list[str] = []
    timings: dict[str, object] = {"source": source}
    started = time.perf_counter()
    async with Client(transport, timeout=300) as client:
        tools = await client.list_tools()
        names = ", ".join(f"`{t.name}`" for t in tools)
        sections.append(f"## tools/list\n\n{names}\n")
        for n, (name, arguments) in enumerate(CALLS):
            call_started = time.perf_counter()
            result = await client.call_tool(name, arguments, raise_on_error=False)
            elapsed = time.perf_counter() - call_started
            if n == 0:
                timings["first_call_seconds"] = round(time.perf_counter() - started, 1)
            text = result.content[0].text
            args = json.dumps(arguments, ensure_ascii=False)
            sections.append(
                f"## {name}\n\n`{args}` · {elapsed:.2f} s · "
                f"{'error' if result.is_error else 'ok'}\n\n````markdown\n{text.rstrip()}\n````\n"
            )
            print(f"\n=== {name} {args} ({elapsed:.2f}s)\n{text}")
        status = await client.read_resource("leyes://estado")
        timings["status"] = json.loads(status[0].text)
    return sections, timings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write docs/demo.md")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="mcp-leyes-demo-") as cache:
        sections, timings = asyncio.run(run(cache))
        size = sum(f.stat().st_size for f in Path(cache).rglob("*") if f.is_file())
    status = timings["status"]
    summary = (
        f"First call (`list_laws`) with an empty cache, including the first sync from "
        f"`{timings['source']}`: {timings['first_call_seconds']} s. Cache after the sync: "
        f"{size / 1e6:.0f} MB ({status['versions']} versions, {status['sections']:,} indexed "
        f"sections, leyes-mx at `{status['head'][:7]}`)."
    )
    print("\n" + summary)
    if args.write:
        header = (
            "# Demo transcript\n\n"
            f"Recorded on {today_mx().isoformat()} with `uv run python scripts/demo.py --write`: "
            "a real MCP client talking to `mcp-leyes` over stdio, with the real leyes-mx "
            "history. Nothing below was edited.\n\n"
            f"{summary} Later calls read from the local clone and index; their timings are "
            "shown with each call.\n\n"
        )
        DOCS.parent.mkdir(exist_ok=True)
        DOCS.write_text(header + "\n".join(sections), encoding="utf-8")
        print(f"wrote {DOCS}")


if __name__ == "__main__":
    main()
