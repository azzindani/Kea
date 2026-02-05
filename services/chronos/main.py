from fastapi import FastAPI
import uvicorn
from shared.logging import get_logger

logger = get_logger(__name__)

app = FastAPI(title="Chronos")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "chronos"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8006)
