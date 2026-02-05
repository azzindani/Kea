from fastapi import FastAPI, HTTPException
import uvicorn
from shared.logging import get_logger

logger = get_logger(__name__)

app = FastAPI(title="The Vault")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "vault"}

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from services.vault.core.audit_trail import get_audit_trail, AuditEventType, configure_audit_trail

# Initialize Audit Backend (Lazy load with Postgres priority)
# configure_audit_trail(SQLiteBackend("data/audit_trail.db")) <- REMOVED for Postgres-only compliance


class LogEventRequest(BaseModel):
    event_type: str
    action: str
    actor: str = "system"
    resource: str = ""
    details: Dict[str, Any] = {}
    session_id: str = ""

@app.post("/audit/logs")
async def log_event(request: LogEventRequest):
    """Log an audit event."""
    audit = get_audit_trail()
    
    # Map string event type to Enum if possible, else generic
    try:
        event_type = AuditEventType(request.event_type)
    except ValueError:
        # Fallback logic or error, existing code assumes exact match
        # Let's try to map string to enum by value
        try:
           event_type = AuditEventType(request.event_type.lower())
        except ValueError:
             # Just fail or use generic if added? Let's assume correct input for now
             # Or catch and return 400
             raise HTTPException(status_code=400, detail=f"Invalid event type: {request.event_type}")

    entry_id = await audit.log(
        event_type=event_type,
        action=request.action,
        actor=request.actor,
        resource=request.resource,
        details=request.details,
        session_id=request.session_id,
    )
    return {"entry_id": entry_id}

@app.get("/audit/logs")
async def search_logs(
    limit: int = 100,
    actor: str = None,
    session_id: str = None
):
    """Search audit logs."""
    audit = get_audit_trail()
    entries = await audit.query(limit=limit, actor=actor, session_id=session_id)
    return {"entries": [e.to_dict() for e in entries]}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)
