import pytest

import asyncio
import sys
import os

# Add root to path
sys.path.append(os.getcwd())

async def main():
    print("🧪 Verifying Research Graph Compilation...")
    try:
        from services.orchestrator.core.graph import compile_research_graph
        graph = compile_research_graph()
        print("\033[92m✅\033[0m Graph Compiled Successfully.")
        return 0
    except Exception as e:
        print(f"❌ Graph Compilation Failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))


@pytest.mark.asyncio
async def test_main():
    await verify()

