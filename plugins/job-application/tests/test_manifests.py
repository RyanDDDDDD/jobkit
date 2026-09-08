"""The Claude Code and Cursor packaging manifests must stay in lockstep:
same plugin name, same version, and every path they name must exist."""
import json
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parents[1]          # plugins/job-application
REPO = PLUGIN.parents[1]                               # repo root


def _load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


CLAUDE_PLUGIN = _load(PLUGIN / ".claude-plugin" / "plugin.json")
CURSOR_PLUGIN = _load(PLUGIN / ".cursor-plugin" / "plugin.json")
CLAUDE_MKT = _load(REPO / ".claude-plugin" / "marketplace.json")
CURSOR_MKT = _load(REPO / ".cursor-plugin" / "marketplace.json")


def test_plugin_name_matches():
    assert CLAUDE_PLUGIN["name"] == CURSOR_PLUGIN["name"] == "job-application"


def test_plugin_version_matches():
    assert CLAUDE_PLUGIN["version"] == CURSOR_PLUGIN["version"]


def test_marketplace_sources_match():
    cs = CLAUDE_MKT["plugins"][0]["source"]
    xs = CURSOR_MKT["plugins"][0]["source"]
    assert cs == xs == "./plugins/job-application"
    assert (REPO / cs.lstrip("./")).is_dir()


def test_shared_component_dirs_exist():
    assert (PLUGIN / "skills").is_dir()
    assert (PLUGIN / "agents").is_dir()
    for sk in ("setup", "apply", "interview"):
        assert (PLUGIN / "skills" / sk / "SKILL.md").is_file()
    for ag in ("sot-retriever", "company-researcher"):
        assert (PLUGIN / "agents" / f"{ag}.md").is_file()


def test_cursor_manifest_minimal_valid():
    assert CURSOR_PLUGIN["name"].islower() and " " not in CURSOR_PLUGIN["name"]


MCP_CLAUDE = _load(PLUGIN / ".mcp.json")
MCP_CURSOR = _load(PLUGIN / "mcp.json")


def test_mcp_bodies_match():
    assert MCP_CLAUDE == MCP_CURSOR


def test_mcp_declares_tavily_via_npx():
    srv = MCP_CLAUDE["mcpServers"]["tavily"]
    assert srv["command"] == "npx"
    assert "tavily-mcp" in srv["args"]
    assert srv["env"]["TAVILY_API_KEY"] == "${TAVILY_API_KEY}"


def test_cursor_declares_the_tavily_variable():
    props = CURSOR_PLUGIN["variables"]["properties"]
    assert "TAVILY_API_KEY" in props


def test_no_api_key_literal_in_repo():
    for p in (PLUGIN / ".mcp.json", PLUGIN / "mcp.json"):
        assert "tvly-" not in p.read_text(encoding="utf-8")
