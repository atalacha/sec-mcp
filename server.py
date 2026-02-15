import sys
import asyncio
import mcp.types as types
from mcp.server import Server, NotificationOptions
from mcp.server.stdio import stdio_server

# Import your auth and tools
from utils.auth import get_credentials, get_people_service, get_storage_client
from tools.contacts import GetListContacts, CreateContacts
from tools.gcs import GetFileFromGCS

# --- 1. SETUP AUTHENTICATION ---
# We do this at the global scope so it happens once on startup
print("Initializing Google Services...", file=sys.stderr)
creds = get_credentials()
people_service = get_people_service(creds)
storage_client = get_storage_client(creds)
print("✅ Services ready.", file=sys.stderr)

# --- 2. INITIALIZE TOOLS ---
# We inject the authenticated services into the tool classes
tool_instances = [
    GetListContacts(people_service),
    CreateContacts(people_service),
    GetFileFromGCS(storage_client)
]

# Create a map for easy lookup by name
tool_map = {tool.name: tool for tool in tool_instances}

# --- 3. CONFIGURE MCP SERVER ---
app = Server("google-workspace-mcp")

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """Expose the tools to the MCP client."""
    return [
        types.Tool(
            name=tool.name,
            description=tool.description,
            inputSchema=tool.input_schema
        )
        for tool in tool_instances
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Execute the tool."""
    if name not in tool_map:
        raise ValueError(f"Unknown tool: {name}")

    try:
        # Run the tool logic
        result = await tool_map[name].run(arguments)
        
        # Return result as text
        return [types.TextContent(type="text", text=str(result))]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error executing {name}: {str(e)}")]

# --- 4. RUN SERVER ---
async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
