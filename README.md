# SecureAgentCore

A secure AI agent application built with Python, FastAPI, Strands Agents, Ollama, and the Model Context Protocol (MCP).

The project demonstrates API-key authentication, role-based access control (RBAC), restricted MCP tools, security audit logging, request tracing, and automated API testing.

## Features

- **AI Agent:** Uses the Strands Agents framework with the local Ollama model `llama3.2:3b`.
- **FastAPI:** Provides REST endpoints for agent interaction.
- **API-Key Authentication:** Protects the chat endpoint.
- **Role-Based Access Control:** Supports employee, HR, and admin roles.
- **MCP Integration:** Connects the agent to employee lookup and inventory tools.
- **Audit Logging:** Records authentication, authorization, and agent execution events.
- **Admin Audit Endpoint:** Allows the configured admin API key to retrieve recent audit events.
- **Request Tracing:** Generates an `X-Request-ID` response header and records request timing.
- **Automated Tests:** Uses pytest and FastAPI TestClient to test application behavior.

## Technology Stack

- Python 3.11
- FastAPI
- Strands Agents
- Ollama
- Model Context Protocol (MCP)
- Pydantic
- pytest

## Project Structure

```text
SecureAgentCore/
├── app/
│   ├── main.py
│   ├── audit.py
│   ├── config.py
│   ├── security.py
│   └── tools/
│       └── mcp_server.py
├── logs/
│   └── security_audit.jsonl
├── tests/
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

The exact test-file location and dependency-file name may differ depending on the local setup.

## Prerequisites

- Python 3.11
- Ollama installed and running
- The `llama3.2:3b` model downloaded
- Project dependencies installed

Download the model with:

```powershell
ollama pull llama3.2:3b
```

Start Ollama if it is not already running.

## Configuration

Create a `.env` file in the project root:

```env
SECURE_AGENT_API_KEY=replace-with-a-strong-random-secret
```

Keep `.env` out of version control. Do not commit real API keys.

## Run the Application

Activate your virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Start the API:

```powershell
uvicorn app.main:app --reload
```

Open the interactive API documentation:

http://127.0.0.1:8000/docs

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Check application health |
| POST | `/chat` | Send a message to the AI agent |
| GET | `/admin/audit` | Retrieve recent audit events |

### Chat Request

Send a POST request to `/chat` with the `X-API-Key` header and this JSON body:

```json
{
  "message": "Check laptop stock"
}
```

Development role keys configured in `app/security.py`:

- Employee: `employee-dev-key`
- HR: `hr-dev-key`
- Admin: the value configured in `.env`

### Role Permissions

| Role | Permitted tools |
|---|---|
| Employee | `inventory_check` |
| HR | `employee_lookup` |
| Admin | `inventory_check`, `employee_lookup` |

The admin audit endpoint requires the configured admin API key.

## Audit Logging and Request Tracing

Audit events are written to:

```text
logs/security_audit.jsonl
```

Each API response includes:

- `X-Request-ID` — identifies the request in logs.
- `X-Process-Time-Ms` — reports processing time in milliseconds.

The current implementation generates request IDs on the server. The audit events do not yet consistently include the request ID, so cross-referencing every audit event with its HTTP request requires a future enhancement.

## Run Tests

With the virtual environment activated:

```powershell
pytest -v
```

The current test suite contains 15 passing tests covering health checks, authentication, role permissions, audit access, request limits, and request IDs.

## Security Notes

This is a learning project, not a production security certification.

Before production deployment:

- Replace development role keys with a managed identity provider or secure credential store.
- Use HTTPS and proper secret management.
- Avoid passing trusted authorization decisions through untrusted process arguments.
- Add rate limiting and stronger input and output controls.
- Ensure audit logs are protected against unauthorized modification.
- Add monitoring, retention policies, and alerting.
- Use a production-ready authentication and authorization design.

## Future Enhancements

- Deploy the agent using AWS Bedrock AgentCore Runtime.
- Integrate AWS identity and managed secrets.
- Improve observability and request-to-audit correlation.
- Add production deployment configuration and monitoring.
