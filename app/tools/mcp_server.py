
import sys

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("secure-business-tools")

# The role is supplied by the local FastAPI application
# when it launches this MCP server process.
ROLE = sys.argv[1] if len(sys.argv) > 1 else "unauthorized"

ROLE_PERMISSIONS = {
    "employee": {"inventory_check"},
    "hr": {"employee_lookup"},
    "admin": {"inventory_check", "employee_lookup"},
}

EMPLOYEES = {
    "EMP001": {"name": "Arun", "department": "IT"},
    "EMP002": {"name": "Priya", "department": "HR"},
}

INVENTORY = {
    "laptop": 10,
    "keyboard": 25,
    "mouse": 30,
}


def check_permission(tool_name: str) -> None:
    allowed_tools = ROLE_PERMISSIONS.get(ROLE, set())

    if tool_name not in allowed_tools:
        raise PermissionError(
            f"Role '{ROLE}' cannot access '{tool_name}'."
        )


@mcp.tool()
def employee_lookup(employee_id: str) -> dict:
    """Look up an employee using their employee ID."""
    check_permission("employee_lookup")

    employee = EMPLOYEES.get(employee_id)

    if employee is None:
        return {"error": "Employee not found"}

    return {"employee_id": employee_id, **employee}


@mcp.tool()
def inventory_check(item: str) -> dict:
    """Check the available stock of an item."""
    check_permission("inventory_check")

    quantity = INVENTORY.get(item.lower())

    if quantity is None:
        return {"error": "Item not found"}

    return {
        "item": item.lower(),
        "available_quantity": quantity,
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
