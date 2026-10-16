
import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    project_root = Path(__file__).resolve().parent
    server_file = project_root / "app" / "tools" / "mcp_server.py"

    server = StdioServerParameters(
        command=sys.executable,
        args=[str(server_file)],
    )

    async with stdio_client(server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Available tools:")
            for tool in tools.tools:
                print("-", tool.name)

            employee = await session.call_tool(
                "employee_lookup",
                {"employee_id": "EMP001"},
            )
            print("\nEmployee lookup result:")
            print(employee.content)

            inventory = await session.call_tool(
                "inventory_check",
                {"item": "laptop"},
            )
            print("\nInventory check result:")
            print(inventory.content)


if __name__ == "__main__":
    asyncio.run(main())
