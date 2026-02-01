
import pytest
import asyncio
import logging
from typing import List, Dict

from services.mcp_host.core.session_registry import SessionRegistry
from shared.mcp.client import MCPClient

# Configure logging to capture server output
logger = logging.getLogger(__name__)

class TestMCPServerConnectivity:
    """
    Systematic Integration Test for MCP Servers.
    
    Verifies:
    1. Discovery: SessionRegistry can find the server.
    2. Spawning: The server process starts successfully (JIT/UV).
    3. Connectivity: MCP Client can establish a session.
    4. Functionality: list_tools() returns valid tool definitions.
    """

    @pytest.fixture(scope="module")
    def registry(self):
        """Shared registry for the test session."""
        return SessionRegistry()

    @pytest.fixture(scope="module")
    def discovered_servers(self, registry):
        """Auto-detect all available servers."""
        return list(registry.server_configs.keys())

    @pytest.mark.asyncio
    async def test_server_discovery(self, discovered_servers):
        """Ensure we are actually finding servers."""
        assert len(discovered_servers) > 0, "No MCP servers were discovered!"
        logger.info(f"✅ Discovered {len(discovered_servers)} servers: {discovered_servers}")

    @pytest.mark.asyncio
    async def test_server_tools_availability(self, registry, discovered_servers):
        """
        Dynamically generate a test for each server.
        NOTE: This runs as one large async test loop to avoid pytest param complexity with async fixtures.
        Ideally we'd fail soft on distinct servers, but this is a 'Smoke Suite'.
        """
        failed_servers = []
        passed_servers = []
        
        # Increase timeout for JIT installations (some servers imply heavy deps)
        TIMEOUT_PER_SERVER = 30 
        
        print(f"\n🚀 Starting Connectivity Tets for {len(discovered_servers)} Servers...")
        
        for server_name in discovered_servers:
            print(f"   Testing {server_name}...", end="", flush=True)
            try:
                # 1. Spawn Session
                # Using wait_for to enforce strict bounds per server
                session = await asyncio.wait_for(
                    registry.get_session(server_name), 
                    timeout=TIMEOUT_PER_SERVER
                )
                
                # 2. Call list_tools
                tools = await session.list_tools()
                
                # 3. Validation
                if not tools:
                    # Some servers might legitimately have 0 tools (e.g. passive resources), 
                    # but usually this indicates a problem in mapping.
                    # We'll log a warning but pass for now if connectivity worked.
                    logger.warning(f"⚠️ {server_name} returned 0 tools.")
                    print(" ⚠️ (0 tools)", end="")
                
                # Check tool structure
                for tool in tools:
                    assert tool.name, f"Tool in {server_name} missing name"
                
                passed_servers.append(server_name)
                print(" ✅ OK")
                
            except asyncio.TimeoutError:
                err_msg = f"❌ Timeout ({TIMEOUT_PER_SERVER}s) - likely install hanging"
                logger.error(f"{server_name}: {err_msg}")
                failed_servers.append((server_name, err_msg))
                print(" ❌ TIMEOUT")
                
            except Exception as e:
                err_msg = f"❌ Error: {str(e)}"
                logger.error(f"{server_name}: {err_msg}")
                failed_servers.append((server_name, err_msg))
                print(f" ❌ ERROR")
                
            finally:
                # Cleanup session immediately to free resources
                if server_name in registry.active_sessions:
                    try:
                        await registry.active_sessions[server_name].close()
                        del registry.active_sessions[server_name]
                    except:
                        pass

        # Final Report
        print("\n📊 Verification Summary:")
        print(f"   Passed: {len(passed_servers)}")
        print(f"   Failed: {len(failed_servers)}")
        
        if failed_servers:
            print("\n❌ Failures:")
            for name, err in failed_servers:
                print(f"   - {name}: {err}")
            
            pytest.fail(f"{len(failed_servers)}/{len(discovered_servers)} servers failed verification.")

if __name__ == "__main__":
    # Allow running directly script for debug
    import sys
    sys.exit(pytest.main(["-v", __file__]))
