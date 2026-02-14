"""
Knowledge File Indexer.

Scans the knowledge/ and configs/knowledge/ directories and converts
Markdown skill/rule files plus YAML domain configs into registry-ready items.

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

# Optional YAML support
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
# YAML domain config scanner (configs/knowledge/)
# ---------------------------------------------------------------------------


def _format_steps(steps: list | str) -> str:
    if isinstance(steps, str):
        return steps
    return "\n".join(f"{i + 1}. {step}" for i, step in enumerate(steps))


def _scan_yaml_knowledge_dir(
    configs_knowledge_dir: Path,
    domain_filter: str | None = None,
    category_filter: str | None = None,
) -> list[dict[str, Any]]:
    """
    Scan configs/knowledge/ YAML files and convert each procedure/rule/skill
    entry to an individual knowledge item.
    """
    if not _HAS_YAML:
        return []

    items: list[dict[str, Any]] = []

    for yaml_file in configs_knowledge_dir.glob("*.yaml"):
        try:
            data = _yaml.safe_load(yaml_file.read_text(encoding="utf-8")) or {}
        except Exception:
            continue

        domain: str = str(data.get("domain", yaml_file.stem)).lower()

        if domain_filter and domain != domain_filter.lower():
            continue

        # ── Procedures ──────────────────────────────────────────────────────
        if not category_filter or category_filter == "procedure":
            for proc_key, proc in (data.get("procedures") or {}).items():
                desc: str = proc.get("description", proc_key.replace("_", " ").title())
                steps_raw = proc.get("steps", [])
                content_lines = [f"## {desc}\n", _format_steps(steps_raw)]
                if proc.get("output"):
                    content_lines.append(f"\n### Output\n{proc['output']}")
                if proc.get("when_to_use"):
                    content_lines.append(f"\n### When to Use\n{proc['when_to_use']}")

                items.append(
                    {
                        "knowledge_id": f"domain_config/{domain}/procedures/{proc_key}",
                        "name": desc,
                        "description": desc,
                        "domain": domain,
                        "category": "procedure",
                        "tags": [domain, "procedure", proc_key],
                        "content": "\n".join(content_lines),
                        "metadata": {"source_file": str(yaml_file.name)},
                    }
                )

        # ── Rules ────────────────────────────────────────────────────────────
        if not category_filter or category_filter == "rule":
            for rule_key, rule_val in (data.get("rules") or {}).items():
                if isinstance(rule_val, list):
                    rule_content = "\n".join(f"- {item}" for item in rule_val)
                    rule_desc = rule_key.replace("_", " ").title()
                elif isinstance(rule_val, dict):
                    rule_content = "\n".join(f"- **{k}**: {v}" for k, v in rule_val.items())
                    rule_desc = rule_val.get("description", rule_key.replace("_", " ").title())
                else:
                    rule_content = str(rule_val)
                    rule_desc = rule_key.replace("_", " ").title()

                items.append(
                    {
                        "knowledge_id": f"domain_config/{domain}/rules/{rule_key}",
                        "name": f"{domain.title()} Rule: {rule_desc}",
                        "description": f"Rule for {domain} domain: {rule_desc}",
                        "domain": domain,
                        "category": "rule",
                        "tags": [domain, "rule", rule_key],
                        "content": f"## {rule_desc}\n\n{rule_content}",
                        "metadata": {"source_file": str(yaml_file.name)},
                    }
                )

        # ── Skills ───────────────────────────────────────────────────────────
        if not category_filter or category_filter == "skill":
            for skill_key, skill_val in (data.get("skills") or {}).items():
                if isinstance(skill_val, dict):
                    skill_desc = skill_val.get("description", skill_key.replace("_", " ").title())
                    steps_raw = skill_val.get("steps", [])
                    content = f"## {skill_desc}\n\n{_format_steps(steps_raw)}"
                else:
                    skill_desc = skill_key.replace("_", " ").title()
                    content = str(skill_val)

                items.append(
                    {
                        "knowledge_id": f"domain_config/{domain}/skills/{skill_key}",
                        "name": skill_desc,
                        "description": skill_desc,
                        "domain": domain,
                        "category": "skill",
                        "tags": [domain, "skill", skill_key],
                        "content": content,
                        "metadata": {"source_file": str(yaml_file.name)},
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
    2. {knowledge_dir}/../configs/knowledge/*.yaml  — Domain YAML configs

    Args:
        knowledge_dir: Path to the knowledge/ directory (contains skills/, rules/)
        domain_filter: If set, only include items matching this domain
        category_filter: If set, only include items matching this category

    Returns:
        List of knowledge item dicts ready for PostgresKnowledgeRegistry.sync_knowledge()
    """
    items: list[dict[str, Any]] = []

    # 1. Markdown files
    if knowledge_dir.exists():
        items.extend(_scan_markdown_files(knowledge_dir, domain_filter, category_filter))

    # 2. YAML domain configs (sibling configs/knowledge/ directory)
    configs_knowledge_dir = knowledge_dir.parent / "configs" / "knowledge"
    if configs_knowledge_dir.exists():
        items.extend(
            _scan_yaml_knowledge_dir(configs_knowledge_dir, domain_filter, category_filter)
        )

    return items


if __name__ == "__main__":
    import json
    import sys

    _dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent
    result = scan_knowledge_files(_dir)
    print(json.dumps(result, indent=2, default=str))
    print(f"\nTotal items: {len(result)}", file=sys.stderr)
