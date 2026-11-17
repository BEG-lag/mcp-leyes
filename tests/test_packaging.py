"""Keep the version, server.json, Dockerfile and docs in step (MCP Registry metadata)."""

import json
import re
import tomllib
from pathlib import Path

import pytest

from mcp_leyes import __version__

ROOT = Path(__file__).resolve().parent.parent
IMAGE = "ghcr.io/beg-lag/mcp-leyes"
SERVER = json.loads((ROOT / "server.json").read_text(encoding="utf-8"))
EM_DASH = chr(0x2014)  # spelled as a code point so this file passes its own check


def test_pyproject_version_matches_package() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["version"] == __version__


def test_server_json_version_and_image_tag() -> None:
    assert SERVER["version"] == __version__
    (package,) = SERVER["packages"]
    assert package["registryType"] == "oci"
    assert package["identifier"] == f"{IMAGE}:{__version__}"
    assert "version" not in package  # the registry rejects it for OCI packages


def test_server_json_name_and_description() -> None:
    assert SERVER["name"] == "io.github.BEG-lag/mcp-leyes"  # GitHub namespace, case-sensitive
    assert len(SERVER["description"]) <= 100


def test_dockerfile_label_proves_ownership() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    label = re.search(r'io\.modelcontextprotocol\.server\.name="([^"]+)"', dockerfile)
    assert label, "Dockerfile must set the io.modelcontextprotocol.server.name label"
    assert label.group(1) == SERVER["name"]


def test_readme_carries_mcp_name() -> None:
    assert f"mcp-name: {SERVER['name']}" in (ROOT / "README.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("name", ["README.md", "README.es.md", "Dockerfile", "server.json"])
def test_pinned_image_tags_are_current(name: str) -> None:
    text = (ROOT / name).read_text(encoding="utf-8")
    tags = set(re.findall(re.escape(IMAGE) + r":(\d+\.\d+\.\d+)", text))
    assert tags <= {__version__}, f"{name} pins {sorted(tags)}, current is {__version__}"


def test_no_em_dash_in_authored_files() -> None:
    """House style: no em dash in anything written for this project (quoted law aside)."""
    skip = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", "docs", "uv.lock"}
    offenders = []
    for path in ROOT.rglob("*"):
        if path.is_dir() or any(part in skip for part in path.relative_to(ROOT).parts):
            continue
        if path.suffix not in {".py", ".md", ".toml", ".yml", ".yaml", ".json", ".svg", ""}:
            continue
        try:
            if EM_DASH in path.read_text(encoding="utf-8"):
                offenders.append(str(path.relative_to(ROOT)))
        except UnicodeDecodeError:
            continue
    assert offenders == []
