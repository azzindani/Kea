from fastapi import FastAPI
import uvicorn
from shared.logging import get_logger

logger = get_logger(__name__)

app = FastAPI(title="Swarm Manager")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "swarm_manager"}

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from services.swarm_manager.core.compliance import get_compliance_engine, ComplianceStandard, ComplianceReport

class ComplianceCheckRequest(BaseModel):
    operation: str
    context: Dict[str, Any]
    standards: Optional[List[str]] = None

@app.post("/compliance/check")
async def check_compliance(request: ComplianceCheckRequest):
    """Check operation against compliance standards."""
    engine = get_compliance_engine()
    
    # Map standards
    standards = None
    if request.standards:
        standards = []
        for s in request.standards:
            try:
                standards.append(ComplianceStandard(s))
            except ValueError:
                # Try fallback or ignore
                 try:
                    standards.append(ComplianceStandard(s.lower()))
                 except ValueError:
                    continue

    report = await engine.check_operation(
        operation=request.operation,
        context=request.context,
        standards=standards,
    )
    
    return {
        "passed": report.passed,
        "summary": report.summary,
        "issues": [
            {
                "check_id": i.check_id,
                "severity": i.severity.value,
                "message": i.message,
                "details": i.details,
            }
            for i in report.issues
        ],
        "checks_passed": report.checks_passed,
        "checks_failed": report.checks_failed,
        "checks_warned": report.checks_warned,
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005)
