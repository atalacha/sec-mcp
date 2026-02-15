import os
import sys
import uvicorn
import mcp.types as types
from mcp.server import Server
from mcp.server.sse import SseServerTransport

# Import your auth and tools
from utils.auth import get_credentials, get_people_service, get_storage_client
from tools.contacts import GetListContacts, CreateContacts
from tools.gcs import GetFileFromGCS

# --- 1. SETUP RESOURCES ---
print("Initializing resources...", file=sys.stderr)
try:
    creds = get_credentials()
    people_service = get_people_service(creds)
    storage_client = get_storage_client(creds)
    print("✅ Resources ready.", file=sys.stderr)
except Exception as e:
    print(f"❌ Error initializing resources: {e}", file=sys.stderr)
    sys.exit(1)

tool_instances = [
    GetListContacts(people_service),
    CreateContacts(people_service),
    GetFileFromGCS(storage_client)
]
tool_map = {tool.name: tool for tool in tool_instances}

# --- 2. SETUP MCP SERVER ---
mcp_server = Server("google-workspace-mcp")

@mcp_server.list_tools()
async def list_tools() -> list[types.Tool]:
    print("📋 Listing tools...", file=sys.stderr)
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
    print(f"🛠️ Tool Called: {name} with args: {arguments}", file=sys.stderr)
    if name not in tool_map:
        raise ValueError(f"Unknown tool: {name}")

    try:
        result = await tool_map[name].run(arguments)
        print(f"✅ Tool {name} executed successfully", file=sys.stderr)
        return [types.TextContent(type="text", text=str(result))]
    except Exception as e:
        print(f"❌ Error executing {name}: {str(e)}", file=sys.stderr)
        return [types.TextContent(type="text", text=f"Error executing {name}: {str(e)}")]

# --- 3. WEB SERVER (PURE ASGI) ---
# We configure the transport to tell the client: "POST your messages to /messages"
sse = SseServerTransport("/messages")

async def app(scope, receive, send):
    """
    A simple raw ASGI application that routes requests manually.
    This avoids Starlette/FastAPI wrapping issues entirely.
    """
    if scope["type"] != "http":
        return

    path = scope["path"]
    method = scope["method"]

    # Route 1: The SSE Stream (GET /sse)
    if path == "/sse" and method == "GET":
        print(f"➡️ Client connected to SSE stream", file=sys.stderr)
        async with sse.connect_sse(scope, receive, send) as streams:
            await mcp_server.run(
                streams[0], streams[1], mcp_server.create_initialization_options()
            )
            
    # Route 2: The Message Handler (POST /messages)
    elif (path == "/messages" or path == "/") and method == "POST":
        print(f"📩 Received POST message on {path}", file=sys.stderr)
        # Add CORS headers
        headers = [
            (b"access-control-allow-origin", b"*"),
            (b"access-control-allow-methods", b"POST, GET, OPTIONS"),
            (b"access-control-allow-headers", b"content-type"),
        ]
        if method == "OPTIONS":
            await send({"type": "http.response.start", "status": 204, "headers": headers})
            await send({"type": "http.response.body", "body": b""})
            return
        await sse.handle_post_message(scope, receive, send)

    # Route 3: Health Check / Root (GET /)
    elif path == "/" and method == "GET":
        headers = [(b"content-type", b"text/plain"), (b"access-control-allow-origin", b"*")]
        await send({"type": "http.response.start", "status": 200, "headers": headers})
        await send({"type": "http.response.body", "body": b"MCP Server is running"})
        
    # 404 Not Found for anything else
    else:
        await send({"type": "http.response.start", "status": 404, "headers": []})
        await send({"type": "http.response.body", "body": b"Not Found"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"🚀 Starting Pure ASGI Server on port {port}...", file=sys.stderr)
    uvicorn.run(app, host="0.0.0.0", port=port)
