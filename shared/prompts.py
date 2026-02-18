"""
Agent Prompt Loader.

Reads system prompts from YAML config files so prompts can be edited
independently of Python source code.

Usage:
    from shared.prompts import get_agent_prompt, get_code_prompt

    # In an agent __init__:
    self.system_prompt = get_agent_prompt("generator")

    # In code_generator.py:
    prompt_template = get_code_prompt()
"""

from __future__ import annotations

from functools import cache
from pathlib import Path

import yaml

_CONFIG_ROOT = Path(__file__).parent.parent / "configs"


@cache
def _load(filename: str) -> dict:
    """Load and cache a YAML config file by filename (relative to configs/)."""
    path = _CONFIG_ROOT / filename
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_agent_prompt(agent_name: str, key: str = "system_prompt") -> str:
    """Return a prompt string for a named agent from configs/agents.yaml.

    Args:
        agent_name: One of: generator, critic, judge, router, synthesizer,
                    divergence, synthesis_worker.
        key: Prompt key within the agent block (default: "system_prompt").

    Returns:
        Prompt string, or empty string if not found.
    """
    return _load("agents.yaml").get("agents", {}).get(agent_name, {}).get(key, "")


def get_kernel_config(key: str | None = None) -> object:
    """Return kernel.yaml config dict, or a specific dotted-key value.

    Args:
        key: Optional dotted path e.g. ``"execution.min_valid_output_length"``.
             If None, returns the full config dict.

    Returns:
        Config value at the given key, full dict if key is None, or None if not found.
    """
    data: dict = _load("kernel.yaml")
    if key is None:
        return data
    val: object = data
    for part in key.split("."):
        if isinstance(val, dict):
            val = val.get(part)  # type: ignore[assignment]
        else:
            return None
    return val


def get_complexity_config() -> dict:
    """Return complexity.yaml for complexity.py tier loading."""
    return _load("complexity.yaml")


def get_report_template() -> dict:
    """Return report_template.yaml for synthesizer_node() report assembly."""
    return _load("report_template.yaml")


def get_code_prompt(name: str = "code_generator") -> str:
    """Return the code generation prompt template from configs/code_prompts.yaml.

    The returned string contains ``{task_description}``, ``{facts_summary}``,
    ``{file_artifacts}``, and ``{resolved_data}`` placeholders — use
    ``.format(...)`` to fill them at call time.

    Args:
        name: Block name in code_prompts.yaml (default: "code_generator").

    Returns:
        Prompt template string, or empty string if not found.
    """
    return _load("code_prompts.yaml").get(name, {}).get("code_prompt", "")
