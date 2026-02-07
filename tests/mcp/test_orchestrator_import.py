import pytest

import sys
import os
import asyncio

sys.path.append(os.getcwd())

async def main():
    print("🧪 Verifying Orchestrator Service Import...")
    try:
        from services.orchestrator.main import app
        print("✅ Orchestrator Service Imported Successfully.")
        return 0
    except Exception as e:
        print(f"❌ Orchestrator Import Failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))


@pytest.mark.asyncio
async def test_main():
    await verify()

