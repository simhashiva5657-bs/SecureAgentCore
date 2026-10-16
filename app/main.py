
import json
import logging
import secrets
import sys
import time
import uuid
from collections import deque
from pathlib import Path

from fastapi import (
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Query,
    Request,
)
from pydantic import BaseModel, Field
from strands import Agent
from strands.models.ollama import OllamaModel
from strands.tools.mcp import MCPClient
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client

from app.config import API_KEY
from app.security import get_current_role
from app.audit import AUDIT_FILE, record_event


# --------------------------------------------------
# Logging configuration
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger("secure_agent")


# --------------------------------------------------
# Application configuration
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MCP_SERVER_PATH = PROJECT_ROOT / "app" / "tools" / "mcp_server.py"

model = OllamaModel(
    host="http://localhost:11434",
    model_id="llama3.2:3b",
)

ROLE_PERMISSIONS = {
    "employee": {"inventory_check"},
    "hr": {"employee_lookup"},
    "admin": {"inventory_check", "employee_lookup"},
}


# --------------------------------------------------
# Request model
# --------------------------------------------------

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


# --------------------------------------------------
# FastAPI application
# --------------------------------------------------

app = FastAPI(
    title="SecureAgentCore",
    description=(
        "Secure AI agent with MCP tools, RBAC, "
        "audit logging, and request tracing"
    ),
    version="1.0.0",
)


# --------------------------------------------------
# Request tracing middleware
# --------------------------------------------------

@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    start_time = time.perf_counter()

    try:
        response = await call_next(request)
        duration_ms = (
            time.perf_counter() - start_time
        ) * 1000

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-Ms"] = (
            f"{duration_ms:.2f}"
        )

        logger.info(
            "request_id=%s method=%s path=%s "
            "status=%s duration_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )

        return response

    except Exception:
        logger.exception(
            "request_id=%s Request failed",
            request_id,
        )
        raise


# --------------------------------------------------
# Health endpoint
# --------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "provider": "ollama",
        "model": "llama3.2:3b",
    }


# --------------------------------------------------
# Secure AI chat endpoint
# --------------------------------------------------

@app.post("/chat")
def chat(
    request: ChatRequest,
    role: str = Depends(get_current_role),
):
    allowed_names = ROLE_PERMISSIONS.get(role)

    if allowed_names is None:
        record_event(
            event="authorization",
            outcome="denied",
            role=role,
            details="Unknown role",
        )

        raise HTTPException(
            status_code=403,
            detail="Your role is not authorized",
        )

    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(MCP_SERVER_PATH), role],
    )

    try:
        mcp_client = MCPClient(
            lambda: stdio_client(server_params)
        )

        with mcp_client:
            all_tools = mcp_client.list_tools_sync()

            allowed_tools = [
                tool
                for tool in all_tools
                if tool.tool_name in allowed_names
            ]

            tool_names = [
                tool.tool_name
                for tool in allowed_tools
            ]

            record_event(
                event="agent_tools_selected",
                outcome="success",
                role=role,
                details=f"Tools: {', '.join(tool_names)}",
            )

            if not allowed_tools:
                record_event(
                    event="agent_execution",
                    outcome="denied",
                    role=role,
                    details="No permitted tools available",
                )

                raise HTTPException(
                    status_code=403,
                    detail="No permitted tools available",
                )

            agent = Agent(
                model=model,
                tools=allowed_tools,
            )

            response = agent(request.message)

            record_event(
                event="agent_execution",
                outcome="success",
                role=role,
                details="Agent request completed",
            )

            return {
                "role": role,
                "response": str(response),
            }

    except HTTPException:
        raise

    except Exception:
        record_event(
            event="agent_execution",
            outcome="failure",
            role=role,
            details="Agent execution failed",
        )

        logger.exception("Agent execution failed")

        raise HTTPException(
            status_code=500,
            detail="Agent execution failed",
        )


# --------------------------------------------------
# Admin authentication helper
# --------------------------------------------------

def verify_admin_key(
    x_api_key: str = Header(
        default="",
        alias="X-API-Key",
    ),
):
    if not secrets.compare_digest(x_api_key, API_KEY):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing admin API key",
        )


# --------------------------------------------------
# Admin-only security audit endpoint
# --------------------------------------------------

@app.get("/admin/audit")
def get_audit_logs(
    _: None = Depends(verify_admin_key),
    limit: int = Query(default=20, ge=1, le=100),
):
    if not AUDIT_FILE.exists():
        return {"count": 0, "events": []}

    try:
        with AUDIT_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:
            recent_lines = deque(file, maxlen=limit)

        events = []

        for line in recent_lines:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                logger.warning(
                    "Skipping malformed audit log entry"
                )

        events.reverse()

        return {
            "count": len(events),
            "events": events,
        }

    except OSError:
        logger.exception("Unable to read audit log")

        raise HTTPException(
            status_code=500,
            detail="Unable to read audit logs",
        )
