
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging.main import get_logger

logger = get_logger(__name__)

# In-memory tool registry (persists for lifetime of server process)
TOOL_REGISTRY = {
    "discovered": [],
    "installed": [],
    "pending": [],
}

async def tool_registry_add(package_name: str, tool_type: str = "general", priority: str = "medium", notes: str = "") -> ToolResult:
    """Add tool to registry for tracking."""
    entry = {
        "name": package_name,
        "type": tool_type,
        "priority": priority,
        "notes": notes,
        "status": "discovered",
    }
    
    TOOL_REGISTRY["discovered"].append(entry)
    
    result = f"# ✅ Added to Registry\n\n"
    result += f"**Package**: {package_name}\n"
    result += f"**Type**: {tool_type}\n"
    result += f"**Priority**: {priority}\n"
    result += f"**Notes**: {notes}\n\n"
    result += f"Registry total: {len(TOOL_REGISTRY['discovered'])} discovered\n"
    
    return ToolResult(content=[TextContent(text=result)])

async def tool_registry_list(status: str = None, tool_type: str = None) -> ToolResult:
    """List tools in the registry."""
    result = "# 📋 Tool Registry\n\n"
    
    for status_key in ["discovered", "installed", "pending"]:
        if status and status != status_key:
            continue
        
        items = TOOL_REGISTRY[status_key]
        if tool_type:
            items = [i for i in items if i.get("type") == tool_type]
        
        result += f"## {status_key.title()} ({len(items)})\n\n"
        
        if items:
            result += "| Package | Type | Priority |\n|---------|------|----------|\n"
            for item in items:
                result += f"| {item['name']} | {item['type']} | {item['priority']} |\n"
        else:
            result += "(empty)\n"
        result += "\n"
    
    return ToolResult(content=[TextContent(text=result)])
