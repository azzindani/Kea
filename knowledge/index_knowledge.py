"""
Knowledge File Indexer.

Scans the knowledge/ directory and converts Markdown skill/rule files 
into registry-ready items for the Knowledge Vault.

Expected item format (for PostgresKnowledgeRegistry.sync_knowledge):
    {
        "knowledge_id": str,      # unique ID, e.g. "skills/finance/algo_trader"
        "name": str,
        "description": str,       # short text used for embedding
        "domain": str,
        "category": str,          # "skill" | "rule" | "procedure" | "persona"
        "tags": list[str],
        "content": str,           # full markdown / text content
        "metadata": dict,         # optional extra info
    }

Usage (from RAG service):
    from knowledge.index_knowledge import scan_knowledge_files
    items = scan_knowledge_files(knowledge_dir)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

# Optional YAML support for frontmatter
try:
    import yaml as _yaml

    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """
    Extract YAML frontmatter from a Markdown string.

    Returns (metadata_dict, body_text).  If no frontmatter is found,
    metadata is empty and body is the full text.
    """
    if not text.startswith("---"):
        return {}, text

    end = text.find("\n---", 3)
    if end == -1:
        return {}, text

    fm_block = text[3:end].strip()
    body = text[end + 4 :].lstrip("\n")

    if not _HAS_YAML:
        # Simple fallback: parse key: value pairs
        meta: dict[str, Any] = {}
        for line in fm_block.splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                meta[k.strip()] = v.strip().strip('"')
        return meta, body

    try:
        meta = _yaml.safe_load(fm_block) or {}
    except Exception:
        meta = {}

    return meta, body


def _infer_category(path: Path, meta: dict[str, Any]) -> str:
    """Infer category from path and frontmatter."""
    # Frontmatter 'type' takes priority
    type_val = meta.get("type", "").lower()
    if type_val in ("skill", "rule", "persona", "procedure"):
        return type_val

    # Infer from directory
    parts = path.parts
    if "skills" in parts:
        return "skill"
    if "rules" in parts:
        return "rule"
    if "personas" in parts:
        return "persona"
    if "procedures" in parts:
        return "procedure"

    return "skill"  # default


def _path_to_id(knowledge_dir: Path, filepath: Path) -> str:
    """Convert file path to a stable knowledge_id."""
    rel = filepath.relative_to(knowledge_dir)
    # Remove extension, use forward slashes
    return str(rel.with_suffix("")).replace("\\", "/")


# ---------------------------------------------------------------------------
# Markdown scanner
# ---------------------------------------------------------------------------


def _scan_markdown_files(
    knowledge_dir: Path,
    domain_filter: str | None = None,
    category_filter: str | None = None,
) -> list[dict[str, Any]]:
    """Scan knowledge/ Markdown files with YAML frontmatter."""
    items: list[dict[str, Any]] = []

    for md_file in knowledge_dir.rglob("*.md"):
        # Skip README / documentation files
        if md_file.name.upper() in ("README.MD", "LIBRARY_MANIFEST.MD"):
            continue

        try:
            text = md_file.read_text(encoding="utf-8")
        except Exception:
            continue

        meta, body = _parse_frontmatter(text)

        # Skip files without a name (not knowledge items)
        if not meta.get("name"):
            continue

        name: str = meta.get("name", md_file.stem.replace("_", " ").title())
        description: str = meta.get("description", name)
        domain: str = str(meta.get("domain", "general")).lower()
        category: str = _infer_category(md_file, meta)

        raw_tags = meta.get("tags", [])
        if isinstance(raw_tags, str):
            tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
        elif isinstance(raw_tags, list):
            tags = [str(t) for t in raw_tags]
        else:
            tags = []

        # Apply filters
        if domain_filter and domain != domain_filter.lower():
            continue
        if category_filter and category != category_filter.lower():
            continue

        knowledge_id = _path_to_id(knowledge_dir, md_file)

        items.append(
            {
                "knowledge_id": knowledge_id,
                "name": name,
                "description": description,
                "domain": domain,
                "category": category,
                "tags": tags,
                "content": body.strip() or text.strip(),
                "metadata": {
                    "source_file": str(md_file.relative_to(knowledge_dir)),
                    "version": str(meta.get("version", "1.0")),
                },
            }
        )

    return items


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def scan_knowledge_files(
    knowledge_dir: Path,
    domain_filter: str | None = None,
    category_filter: str | None = None,
) -> list[dict[str, Any]]:
    """
    Scan all knowledge sources and return registry-ready items.

    Sources:
    1. {knowledge_dir}/**/*.md  — Markdown skill/rule files with YAML frontmatter

    Args:
        knowledge_dir: Path to the knowledge/ directory (contains skills/, rules/, procedures/)
        domain_filter: If set, only include items matching this domain
        category_filter: If set, only include items matching this category

    Returns:
        List of knowledge item dicts ready for PostgresKnowledgeRegistry.sync_knowledge()
    """
    items: list[dict[str, Any]] = []

    # Scan all Markdown files in the knowledge directory
    if knowledge_dir.exists():
        items.extend(_scan_markdown_files(knowledge_dir, domain_filter, category_filter))

    return items


if __name__ == "__main__":
    import json
    import sys

    _dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent
    result = scan_knowledge_files(_dir)
    print(json.dumps(result, indent=2, default=str))
    print(f"\nTotal items: {len(result)}", file=sys.stderr)
