
import pytest
import asyncio
import logging
import traceback
from typing import List, Dict

from services.mcp_host.core.session_registry import SessionRegistry
from shared.mcp.client import MCPClient

# Configure logging to capture server output with DEBUG level
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
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
        TIMEOUT_PER_SERVER = 120 
        
        print(f"\n🚀 Starting Connectivity Test for {len(discovered_servers)} Servers...")
        print("=" * 80)
        
        for server_name in discovered_servers:
            print(f"\n📦 Testing {server_name}...", flush=True)
            error_details = None
            
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
                    print(f"   ⚠️ Warning: Server returned 0 tools")
                
                # Check tool structure
                for tool in tools:
                    assert tool.name, f"Tool in {server_name} missing name"
                
                passed_servers.append(server_name)
                print(f"   ✅ OK - {len(tools)} tools registered")
                
            except asyncio.TimeoutError as e:
                error_details = f"Timeout ({TIMEOUT_PER_SERVER}s) - likely install hanging or server crash"
                # Try to get more info from the exception
                if hasattr(e, '__cause__') and e.__cause__:
                    error_details += f"\n   Cause: {e.__cause__}"
                    
                # Check if server is in active processes and try to read stderr
                if server_name in registry.active_processes:
                    proc = registry.active_processes[server_name]
                    if proc.stderr:
                        try:
                            stderr_data = await asyncio.wait_for(proc.stderr.read(8192), timeout=2.0)
                            stderr_text = stderr_data.decode('utf-8', errors='replace').strip()
                            if stderr_text:
                                error_details += f"\n   STDERR:\n{_indent(stderr_text, 6)}"
                        except:
                            pass
                
                logger.error(f"{server_name}: ❌ {error_details}")
                failed_servers.append((server_name, error_details))
                print(f"   ❌ TIMEOUT")
                print(f"   {error_details}")
                
            except Exception as e:
                # Get full traceback for debugging
                tb = traceback.format_exc()
                error_details = f"{type(e).__name__}: {str(e)}"
                
                # Try to capture stderr if process exists
                if server_name in registry.active_processes:
                    proc = registry.active_processes[server_name]
                    if proc.stderr:
                        try:
                            stderr_data = await asyncio.wait_for(proc.stderr.read(8192), timeout=2.0)
                            stderr_text = stderr_data.decode('utf-8', errors='replace').strip()
                            if stderr_text:
                                error_details += f"\n   STDERR:\n{_indent(stderr_text, 6)}"
                        except:
                            pass
                
                logger.error(f"{server_name}: ❌ {error_details}")
                failed_servers.append((server_name, error_details))
                print(f"   ❌ ERROR")
                print(f"   {error_details}")
                # Print truncated traceback for key info
                tb_lines = tb.strip().split('\n')
                if len(tb_lines) > 6:
                    print(f"   Traceback (last 6 lines):")
                    for line in tb_lines[-6:]:
                        print(f"      {line}")
                else:
                    print(f"   Traceback:")
                    for line in tb_lines:
                        print(f"      {line}")
                
            finally:
                # Cleanup session immediately to free resources
                if server_name in registry.active_sessions:
                    try:
                        await registry.active_sessions[server_name].close()
                        del registry.active_sessions[server_name]
                    except:
                        pass
                # Also cleanup process
                if server_name in registry.active_processes:
                    try:
                        proc = registry.active_processes[server_name]
                        proc.terminate()
                        await asyncio.wait_for(proc.wait(), timeout=5.0)
                        del registry.active_processes[server_name]
                    except:
                        pass

        # Final Report
        print("\n" + "=" * 80)
        print("📊 VERIFICATION SUMMARY")
        print("=" * 80)
        print(f"   ✅ Passed: {len(passed_servers)}")
        print(f"   ❌ Failed: {len(failed_servers)}")
        
        if failed_servers:
            print("\n" + "-" * 80)
            print("❌ FAILED SERVERS (Detailed):")
            print("-" * 80)
            for name, err in failed_servers:
                print(f"\n🔴 {name}:")
                for line in err.split('\n'):
                    print(f"   {line}")
            
            pytest.fail(f"{len(failed_servers)}/{len(discovered_servers)} servers failed verification.")


def _indent(text: str, spaces: int = 4) -> str:
    """Indent each line of text."""
    prefix = " " * spaces
    return "\n".join(prefix + line for line in text.split('\n'))


if __name__ == "__main__":
    # Allow running directly script for debug
    import sys
    sys.exit(pytest.main(["-v", "-s", "--tb=short", __file__]))
