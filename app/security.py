
import secrets

from fastapi import Header, HTTPException

from app.audit import record_event
from app.config import API_KEY


USERS = {
    "employee-dev-key": "employee",
    "hr-dev-key": "hr",
    API_KEY: "admin",
}


def get_current_role(
    x_api_key: str = Header(default="", alias="X-API-Key"),
) -> str:
    for key, role in USERS.items():
        if secrets.compare_digest(x_api_key, key):
            record_event(
                event="authentication",
                outcome="success",
                role=role,
                details="API key accepted",
            )
            return role

    record_event(
        event="authentication",
        outcome="failure",
        details="Missing or invalid API key",
    )

    raise HTTPException(
        status_code=401,
        detail="Invalid or missing API key",
    )


def require_role(*allowed_roles: str):
    def check_role(role: str = __import__(
        "fastapi"
    ).Depends(get_current_role)) -> str:
        if role not in allowed_roles:
            record_event(
                event="authorization",
                outcome="denied",
                role=role,
                details="Required role not permitted",
            )

            raise HTTPException(
                status_code=403,
                detail="You do not have permission to perform this action",
            )

        record_event(
            event="authorization",
            outcome="allowed",
            role=role,
            details="Role permission granted",
        )

        return role

    return check_role
