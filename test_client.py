import asyncio
from mcp.client.sse import sse_client
from mcp.types import CallToolRequest, Tool

# We connect to your running local server
SERVER_URL = "http://localhost:8080/sse"

async def main():
    print(f"🔌 Connecting to {SERVER_URL}...")
    
    async with sse_client(SERVER_URL) as (read_stream, write_stream):
        print("✅ Connected!")
        
        # 1. Initialize the session
        # We start the conversation with the server
        from mcp.client.session import ClientSession
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            
            # 2. List Available Tools
            print("\n🔍 Asking server: 'What tools do you have?'")
            tools = await session.list_tools()
            
            print(f"   Found {len(tools.tools)} tools:")
            for t in tools.tools:
                print(f"   - 📦 {t.name}: {t.description}")

            # 3. Test a specific tool (Optional)
            # Only runs if you have the 'get_list_contacts' tool
            target_tool = "get_list_contacts"
            if any(t.name == target_tool for t in tools.tools):
                print(f"\n🚀 Testing tool: {target_tool}...")
                result = await session.call_tool(
                    target_tool,
                    arguments={"limit": 5}
                )
                print(f"   Result: {result.content[0].text}")

if __name__ == "__main__":
    asyncio.run(main())
