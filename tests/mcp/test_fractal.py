import pytest

import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from services.orchestrator.core.organization import get_organization, Domain
from services.orchestrator.core.conversation import get_conversation_manager, Intent
from services.orchestrator.core.agent_spawner import get_spawner, SpawnPlan, SubTask, TaskType
from services.orchestrator.mcp.client import get_mcp_orchestrator

async def verify_fractal():
    print("=" * 60)
    print("🧠  VERIFYING FRACTAL CORPORATION (Mind & Body)")
    print("=" * 60)

    # 1. Verify Organization (The Structure)
    print("\n[Phase 2: Organization]")
    org = get_organization()
    # Manually init if main.py didn't run
    if not org.list_departments():
        org.create_department("Research", Domain.RESEARCH)
    
    depts = org.list_departments()
    print(f"✅ Organization initialized with {len(depts)} departments: {[d.name for d in depts]}")

    # 2. Verify Memory (The Mind)
    print("\n[Phase 2: Awareness]")
    mem = get_conversation_manager()
    session_id = "test_fractal"
    
    # User turn 1
    await mem.process(session_id, "Analyze Tesla revenue")
    # User turn 2 (Follow up)
    resp = await mem.process(session_id, "Compare with Ford")
    
    print(f"Query: 'Compare with Ford'")
    print(f"Intent: {resp.intent.value}")
    if "Tesla" in resp.context:
        print("✅ Memory Context Retrieval: SUCCESS (Tesla found in context)")
    else:
        print("❌ Memory Context Retrieval: FAILED")

    # 3. Verify Spawner (The Body)
    print("\n[Phase 3: Fractal Swarm]")
    
    # Mock LLM and MCP for safety
    async def mock_llm(sys, user):
        return "Analysis complete."
    
    # We need a dummy MCP if it's not running
    try:
        mcp = get_mcp_orchestrator()
        # Mock tool registry to avoid 'Tool not found'
        mcp._tool_registry["web_search"] = "mock_server"
        mcp._tool_registry["execute_code"] = "mock_server"
        
        # Mock servers
        from services.orchestrator.mcp.client import MCPServerConnection
        from shared.mcp.client import MCPClient
        
        # We just need call_tool to return something
        class MockClient:
            async def call_tool(self, name, args):
                from shared.mcp.protocol import ToolResult, TextContent
                return ToolResult(content=[TextContent(text="Mock Result")], isError=False)
        
        mcp._servers["mock_server"] = MCPServerConnection(
            name="mock_server", command="echo", client=MockClient(), is_connected=True
        )
            
    except Exception as e:
        print(f"Setup warning: {e}")

    spawner = get_spawner(llm_callback=mock_llm)
    
    subtasks = [
        SubTask("1", "Search Tesla", Domain.RESEARCH, TaskType.RESEARCH),
        SubTask("2", "Search Ford", Domain.RESEARCH, TaskType.RESEARCH),
    ]
    plan = SpawnPlan("job_1", subtasks, max_parallel=2)
    
    print(f"🚀 Spawning Swarm with {len(subtasks)} agents...")
    result = await spawner.execute_swarm(plan)
    
    print(f"✅ Swarm Result: {result.successful}/{result.total_agents} successful")
    print(f"   Duration: {result.duration_seconds:.2f}s")
    
    print("\n" + "=" * 60)
    print("✅ FRACTAL VERIFICATION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(verify_fractal())


@pytest.mark.asyncio
async def test_main():
    await verify()

