import asyncio
import time
from .common_methods import *
from mcp_use import MCPAgent, MCPClient  # Ensure 'mcp_use.py' is in the same directory or installed as a package

import mcp_use
mcp_use.set_debug(1) # 1 - INFO, 2 - DEBUG
import logging
#logging.basicConfig(filename=info_log_file, level=logging.INFO)
# logging.basicConfig(filename=debug_log_file, level=logging.DEBUG)

# 1️⃣ Describe Playwright & other MCP servers as config.
CONFIG = {
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp@latest", "--isolated"]
    }
  }
}

CONFIG_OTHER = {
  "mcpServers": {
    "playwright": {
      "url": "http://localhost:8931/sse"
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y",
        "@modelcontextprotocol/server-filesystem",
        f"{os.path.join(os.getcwd(), step2_path)}"
      ]
    }
  }
}

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
    # 2️⃣ Wire the LLM to the MCP client
    server_status = await test_server_startup()
    global agent
    agent = MCPAgent(llm=llm, client=mcpclient, memory_enabled=False,
                     auto_initialize=True, max_steps=15)
    return server_status
    
# Function to asynchronously execute tasks on MCP
async def execute_mcp_use(prompt: str):
    # 3️⃣ Ask something that requires real web browsing
    result = await agent.run(prompt)
    return result

# Function to asynchronously execute on MCP and return chunks
async def execute_mcp_return_chunk(prompt: str):
    async for chunk in agent.astream(prompt):
        print(chunk["messages"], end="", flush=True)
        yield chunk["messages"]

def close_mcp_client():
    # 4️⃣ Always clean up running MCP sessions
    mcpclient.close_all_sessions()

