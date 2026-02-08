import os
import re
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path("knowledge/skills")
MANIFEST_FILE = Path("knowledge/LIBRARY_MANIFEST.md")

DOMAINS = defaultdict(list)

def parse_frontmatter(content):
    meta = {}
    match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
    if match:
        yaml_block = match.group(1)
        for line in yaml_block.split("\n"):
            if ": " in line:
                key, val = line.split(": ", 1)
                meta[key.strip()] = val.strip().strip('"')
    return meta

def generate_manifest():
    total_skills = 0
    
    # 1. Scan and Parse
    for root, _, files in os.walk(BASE_DIR):
        for file in files:
            if file.endswith(".md"):
                filepath = Path(root) / file
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    meta = parse_frontmatter(content)
                    
                    if "name" in meta:
                        domain = meta.get("domain", "Uncategorized")
                        desc = meta.get("description", "No description")
                        tags = meta.get("tags", "[]") # Raw string like ["tag1", "tag2"]
                        
                        # Clean up tags string for display if needed
                        tags = tags.replace("[", "").replace("]", "").replace('"', "").replace("'", "")
                        
                        entry = {
                            "name": meta["name"],
                            "path": filepath.relative_to("knowledge").as_posix(),
                            "desc": desc,
                            "tags": tags
                        }
                        DOMAINS[domain].append(entry)
                        total_skills += 1

    # 2. Sort Domains and Skills
    sorted_domains = sorted(DOMAINS.keys())
    
    # 3. Generate Markdown Content
    lines = []
    lines.append("# 📚 Kea 'Liquid Intelligence' Library Manifest")
    lines.append(f"> **Total Skills Available**: {total_skills}")
    lines.append("")
    lines.append("This document is an automatically generated index of all available 'Pure Context' skills.")
    lines.append("")
    lines.append("## Table of Contents")
    for domain in sorted_domains:
        anchor = domain.lower().replace(" ", "-")
        count = len(DOMAINS[domain])
        lines.append(f"- [{domain.title()} ({count})](#{anchor})")
    
    lines.append("")
    lines.append("---")
    
    for domain in sorted_domains:
        pretty_domain = domain.title()
        anchor = domain.lower().replace(" ", "-")
        lines.append(f"## {pretty_domain} <a name='{anchor}'></a>")
        
        # Sort skills by name within domain
        skills = sorted(DOMAINS[domain], key=lambda x: x["name"])
        
        # Create a table for each domain
        lines.append("| Skill Name | Description | Tags |")
        lines.append("|---|---|---|")
        
        for skill in skills:
            link = f"[{skill['name']}]({skill['path']})"
            lines.append(f"| **{link}** | {skill['desc']} | `{skill['tags']}` |")
        
        lines.append("") 
        
    # 4. Write to File
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    print(f"Manifest generated at {MANIFEST_FILE} with {total_skills} skills.")

if __name__ == "__main__":
    generate_manifest()
