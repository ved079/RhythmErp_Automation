"""
PC Agent — standalone FastAPI app that runs on each physical PC.
Receives test run requests from the concurrency dispatcher and
streams results back as SSE events.
"""

import os

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from api.models import CreateRunRequest
from api.test_runner import run_tests_stream

app = FastAPI(title="PC Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "pc": os.environ.get("PC_NAME", "unknown"),
    }


@app.post("/run")
def run_endpoint(run_request: CreateRunRequest, x_secret: str = Header(...)):
    secret = os.environ.get("AGENT_SECRET", "")
    if x_secret != secret:
        raise HTTPException(status_code=403, detail="Invalid secret")
    return StreamingResponse(
        run_tests_stream(run_request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("AGENT_HOST", "0.0.0.0")
    port = int(os.environ.get("AGENT_PORT", "8100"))
    uvicorn.run(app, host=host, port=port)
