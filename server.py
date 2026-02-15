import os
import sys
import uvicorn
import mcp.types as types
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.requests import Request
from starlette.responses import Response

# Import your existing auth and tools
from utils.auth import get_credentials, get_people_service, get_storage_client
from tools.contacts import GetListContacts, CreateContacts
from tools.gcs import GetFileFromGCS

# --- 1. SETUP RESOURCES (Same as before) ---
# Note: On Cloud Run, this should ideally use Service Account logic
creds = get_credentials() 
people_service = get_people_service(creds)
storage_client = get_storage_client(creds)

tool_instances = [
    GetListContacts(people_service),
    CreateContacts(people_service),
    GetFileFromGCS(storage_client)
]
tool_map = {tool.name: tool for tool in tool_instances}

# --- 2. SETUP MCP SERVER OBJECT ---
# This is the "brain" of the agent
mcp_server = Server("google-workspace-mcp")

# --- 3. RESTORE THE LOGIC ---
# These are exactly the same as your local version!

@mcp_server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name=tool.name,
            description=tool.description,
            inputSchema=tool.input_schema
        )
        for tool in tool_instances
    ]

@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    if name not in tool_map:
        raise ValueError(f"Unknown tool: {name}")

    try:
        result = await tool_map[name].run(arguments)
        return [types.TextContent(type="text", text=str(result))]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error executing {name}: {str(e)}")]

# --- 4. WEB SERVER ADAPTER (New for Cloud Run) ---
# Instead of stdio, we use HTTP SSE (Server-Sent Events)

sse = SseServerTransport("/messages")

async def handle_sse(request: Request):
    """
    1. Client connects here to start the session.
    2. We upgrade the connection to an SSE stream.
    """
    async with sse.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await mcp_server.run(
            streams[0], streams[1], mcp_server.create_initialization_options()
        )

async def handle_messages(request: Request):
    """
    1. Client sends POST requests here with JSON-RPC commands (call_tool, etc).
    2. We feed them into the MCP server via the transport.
    """
    await sse.handle_post_message(request.scope, request.receive, request._send)

# Define the Starlette App (The actual Web Server)
starlette_app = Starlette(
    debug=True,
    routes=[
        Route("/sse", endpoint=handle_sse),
        Route("/messages", endpoint=handle_messages, methods=["POST"]),
    ],
)

# --- 5. ENTRY POINT ---
if __name__ == "__main__":
    # Cloud Run injects the PORT environment variable
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting SSE Server on port {port}...", file=sys.stderr)
    uvicorn.run(starlette_app, host="0.0.0.0", port=port)
