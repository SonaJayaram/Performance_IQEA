import asyncio
import time
import os
from src.common_methods import llm
from mcp_use import MCPAgent, MCPClient

import mcp_use
mcp_use.set_debug(1)

CONFIG = {
    "mcpServers": {
        "playwright": {
            "command": "npx",
            "args": ["-y", "@playwright/mcp@latest", "--isolated"]
        }
    }
}

mcpclient = None
agent = None

async def test_server_startup():
    start_time = time.time()
    try:
        global mcpclient
        mcpclient = MCPClient.from_dict(CONFIG)
        await asyncio.wait_for(mcpclient.create_all_sessions(), timeout=15)
        elapsed = time.time() - start_time
        print(f"✅ MCP Client Sessions created in {elapsed:.2f}s")
        return True
    except asyncio.TimeoutError:
        elapsed = time.time() - start_time
        print(f"❌ MCP Client Session creation timed out after {elapsed:.2f}s")
        return False

async def start_mcp_client():
    server_status = await test_server_startup()
    global agent
    agent = MCPAgent(llm=llm, client=mcpclient, memory_enabled=False,
                     auto_initialize=True, max_steps=15)
    return server_status

async def execute_mcp_use(prompt: str):
    result = await agent.run(prompt)
    return result

def close_mcp_client():
    mcpclient.close_all_sessions()
