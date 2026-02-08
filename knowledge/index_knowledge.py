"""
Knowledge Indexer.

Scans the knowledge/ directory, parses markdown files with YAML frontmatter,
and indexes them into pgvector via PostgresKnowledgeRegistry.

Usage:
    # Index all knowledge files
    uv run python -m knowledge.index_knowledge

    # Index only finance skills
    uv run python -m knowledge.index_knowledge --domain finance --category skill
"""

from __future__ import annotations

import argparse
import asyncio
import re
import sys
from pathlib import Path
from typing import Any

# Resolve project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """
    Parse YAML frontmatter from markdown content.

    Returns:
        Tuple of (frontmatter dict, body text without frontmatter)
    """
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not match:
        return {}, content

    import yaml

    try:
        frontmatter = yaml.safe_load(match.group(1)) or {}
    except Exception:
        frontmatter = {}

    body = content[match.end() :]
    return frontmatter, body


def detect_category(filepath: Path) -> str:
    """Detect knowledge category from file path."""
    parts = filepath.parts
    for part in parts:
        if part == "skills":
            return "skill"
        elif part == "rules":
            return "rule"
        elif part == "personas":
            return "persona"
        elif part == "memory":
            return "memory"
        elif part == "agents":
            return "agent"
    return "skill"


def detect_domain(filepath: Path, frontmatter: dict[str, Any]) -> str:
    """Detect domain from frontmatter or file path."""
    if "domain" in frontmatter:
        return str(frontmatter["domain"])

    parts = filepath.parts
    knowledge_idx = None
    for i, part in enumerate(parts):
        if part in ("skills", "rules", "personas", "memory"):
            knowledge_idx = i
            break

    if knowledge_idx is not None and knowledge_idx + 1 < len(parts) - 1:
        return parts[knowledge_idx + 1]

    return "general"


def scan_knowledge_files(
    base_dir: Path,
    domain_filter: str | None = None,
    category_filter: str | None = None,
) -> list[dict[str, Any]]:
    """
    Scan knowledge directory for markdown files.

    Returns list of knowledge items ready for indexing.
    """
    items: list[dict[str, Any]] = []

    for md_file in sorted(base_dir.rglob("*.md")):
        # Skip non-content files
        if md_file.name in ("README.md", "LIBRARY_MANIFEST.md"):
            continue

        content = md_file.read_text(encoding="utf-8")
        frontmatter, body = parse_frontmatter(content)

        category = detect_category(md_file)
        domain = detect_domain(md_file, frontmatter)

        # Apply filters
        if domain_filter and domain != domain_filter:
            continue
        if category_filter and category != category_filter:
            continue

        # Build knowledge_id from relative path
        rel_path = md_file.relative_to(base_dir)
        knowledge_id = str(rel_path).replace("/", ".").removesuffix(".md")

        name = frontmatter.get("name", md_file.stem.replace("_", " ").title())
        description = frontmatter.get("description", "")
        if not description:
            # Use first non-empty line of body as description
            for line in body.split("\n"):
                line = line.strip()
                if line and not line.startswith("#"):
                    description = line[:200]
                    break

        tags = frontmatter.get("tags", [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",")]

        items.append(
            {
                "knowledge_id": knowledge_id,
                "name": name,
                "description": description,
                "domain": domain,
                "category": category,
                "tags": tags,
                "content": content,
                "metadata": {
                    "source_file": str(rel_path),
                    "frontmatter": frontmatter,
                },
            }
        )

    return items


async def index_all(
    domain_filter: str | None = None,
    category_filter: str | None = None,
) -> int:
    """Index all knowledge files into pgvector."""
    from shared.knowledge.registry import PostgresKnowledgeRegistry

    knowledge_dir = PROJECT_ROOT / "knowledge"
    if not knowledge_dir.exists():
        print(f"Knowledge directory not found: {knowledge_dir}")
        return 0

    print(f"Scanning {knowledge_dir}...")
    items = scan_knowledge_files(
        knowledge_dir,
        domain_filter=domain_filter,
        category_filter=category_filter,
    )
    print(f"Found {len(items)} knowledge files to index")

    if not items:
        print("No files to index.")
        return 0

    # Group by domain for progress reporting
    domains: dict[str, int] = {}
    for item in items:
        d = item["domain"]
        domains[d] = domains.get(d, 0) + 1

    print("Domains found:")
    for d, count in sorted(domains.items()):
        print(f"  {d}: {count} items")

    registry = PostgresKnowledgeRegistry()

    # Batch in groups of 20 to avoid memory pressure
    total_updated = 0
    batch_size = 20
    for i in range(0, len(items), batch_size):
        batch = items[i : i + batch_size]
        updated = await registry.sync_knowledge(batch)
        total_updated += updated
        print(f"  Indexed batch {i // batch_size + 1}: {updated} new/updated")

    total = await registry.count()
    print(f"\nDone. {total_updated} items indexed. Total in registry: {total}")
    return total_updated


def main() -> None:
    parser = argparse.ArgumentParser(description="Index knowledge files into pgvector")
    parser.add_argument("--domain", help="Filter by domain (e.g., finance)")
    parser.add_argument("--category", help="Filter by category (skill, rule, persona)")
    args = parser.parse_args()

    asyncio.run(index_all(domain_filter=args.domain, category_filter=args.category))


if __name__ == "__main__":
    main()
