
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

AUDIT_FILE = LOG_DIR / "security_audit.jsonl"

audit_logger = logging.getLogger("security_audit")


def record_event(
    event: str,
    outcome: str,
    role: str = "unknown",
    details: str = "",
) -> None:
    """Write one security event as a JSON line."""

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "outcome": outcome,
        "role": role,
        "details": details,
    }

    try:
        with AUDIT_FILE.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record) + "\n")

        audit_logger.info(
            "event=%s outcome=%s role=%s",
            event,
            outcome,
            role,
        )

    except OSError:
        audit_logger.exception("Failed to write security audit event")