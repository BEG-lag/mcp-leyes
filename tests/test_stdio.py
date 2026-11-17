"""Start the real entry point over stdio, the way Claude Desktop and Claude Code do."""

import os
import sys

import pytest
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

from mcp_leyes import __version__

pytestmark = pytest.mark.anyio


async def test_stdio_handshake_and_offline_query(fixture_repo, tmp_path) -> None:
    root, _ = fixture_repo
    env = dict(os.environ)
    env.update({"MCP_LEYES_SOURCE": str(root), "MCP_LEYES_CACHE": str(tmp_path / "cache")})
    transport = StdioTransport(command=sys.executable, args=["-m", "mcp_leyes.server"], env=env)
    async with Client(transport) as client:
        assert client.server_info.name == "leyes"
        assert client.server_info.version == __version__
        names = {tool.name for tool in await client.list_tools()}
        result = await client.call_tool("get_article", {"law": "lfpr", "article": "15-Ñ"})
    assert "get_article" in names
    assert "Los peritos registrados podrán actuar" in result.content[0].text
    assert (tmp_path / "cache").is_dir()


def test_version_flag(capsys) -> None:
    from mcp_leyes.server import main

    with pytest.raises(SystemExit) as exit_info:
        main(["--version"])
    assert exit_info.value.code == 0
    assert capsys.readouterr().out.strip() == f"mcp-leyes {__version__}"


def test_sync_command(fixture_repo, tmp_path, monkeypatch, capsys) -> None:
    import json

    from mcp_leyes import server

    root, _ = fixture_repo
    monkeypatch.setenv("MCP_LEYES_SOURCE", str(root))
    monkeypatch.setenv("MCP_LEYES_CACHE", str(tmp_path / "cache"))
    previous = server._corpus
    server._corpus = None
    try:
        with pytest.raises(SystemExit) as exit_info:
            server.main(["sync"])
    finally:
        if server._corpus is not None:
            server._corpus.close()
        server._corpus = previous
    assert exit_info.value.code == 0
    report = json.loads(capsys.readouterr().out)
    assert report["indexed_versions"] == 4
    assert report["laws"] == 2
    assert report["latest_version"] == "10-03-2020"
