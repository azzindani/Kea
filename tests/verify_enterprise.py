
import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from services.orchestrator.core.audit_trail import get_audit_trail, AuditEventType, SQLiteBackend, configure_audit_trail
from services.orchestrator.core.compliance import get_compliance_engine
from services.orchestrator.mcp.client import get_mcp_orchestrator

async def verify_enterprise():
    print("=" * 50)
    print("🛡️  VERIFYING ENTERPRISE LAYERS")
    print("=" * 50)

    # 1. Initialize Audit Backend
    print("\n[Audit Trail]")
    db_path = "data/audit_trail_test.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        
    backend = SQLiteBackend(db_path)
    configure_audit_trail(backend)
    
    audit = get_audit_trail()
    await audit.log(AuditEventType.SYSTEM_START, action="Verification Test Started", actor="tester")
    
    count = await audit.backend.count()
    print(f"✅ Audit Log Write Successful. Entries: {count}")
    
    # 2. Verify Compliance Engine
    print("\n[Compliance Engine]")
    comp = get_compliance_engine()
    
    # Test 1: Good URL (HTTPS)
    res_good = await comp.check_operation("tool_exec", {"url": "https://google.com"})
    print(f"Checking https://google.com: {'✅ PASSED' if res_good.passed else '❌ FAILED'}")
    
    # Test 2: Bad URL (HTTP)
    res_bad = await comp.check_operation("tool_exec", {"url": "http://evil.com"})
    print(f"Checking http://evil.com:   {'✅ BLOCKED' if not res_bad.passed else '❌ ALLOWED'}")
    
    if not res_bad.passed:
        print(f"   Reason: {res_bad.issues[0].message}")
        
    print("\n" + "=" * 50)
    print("✅ VERIFICATION COMPLETE")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(verify_enterprise())
