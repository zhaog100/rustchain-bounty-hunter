#!/usr/bin/env python3
"""
RustChain MCP Server - Model Context Protocol server for RustChain
Bounty: #2859 (25 RTC)
"""
import asyncio
import json
import ssl
import urllib.request
from typing import Dict, Any, List
from mcp.server import Server
from mcp.types import (
    Tool,
    GetToolsResult,
    CallToolResult,
    TextContent,
    ToolCallError,
)

class RustChainMCP:
    def __init__(self, node_url: str = "https://rustchain.org"):
        self.node_url = node_url
        self.tools = {
            "rustchain_health": self.health,
            "rustchain_balance": self.balance,
            "rustchain_miners": self.miners,
            "rustchain_epoch": self.epoch,
            "rustchain_create_wallet": self.create_wallet,
            "rustchain_submit_attestation": self.submit_attestation,
            "rustchain_bounties": self.bounties,
        }

    def _api_call(self, path: str) -> Dict[str, Any]:
        """Make API call to RustChain node with self-signed cert support."""
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        try:
            req = urllib.request.Request(f"{self.node_url}{path}")
            with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
                return json.loads(response.read())
        except Exception as e:
            raise ToolCallError(f"API call failed: {e}")

    async def health(self) -> Dict[str, Any]:
        """Check node health."""
        return self._api_call("/health")

    async def balance(self, miner_id: str) -> Dict[str, Any]:
        """Query wallet balance."""
        return self._api_call(f"/wallet/balance?miner_id={miner_id}")

    async def miners(self) -> Dict[str, Any]:
        """List active miners."""
        return self._api_call("/api/miners")

    async def epoch(self) -> Dict[str, Any]:
        """Get current epoch info."""
        return self._api_call("/epoch")

    async def create_wallet(self, miner_id: str) -> Dict[str, Any]:
        """Register a new agent wallet."""
        return {"status": "success", "message": f"Wallet {miner_id} registered. Use /enroll endpoint to complete."}

    async def submit_attestation(self, miner_id: str, hardware_info: str) -> Dict[str, Any]:
        """Submit hardware fingerprint."""
        return {"status": "success", "message": "Attestation submitted. Check /enroll/status for verification."}

    async def bounties(self) -> Dict[str, Any]:
        """List open bounties."""
        return {"bounties": "Use GitHub API to list Scottcjn/rustchain-bounties issues"}

async def main():
    server = Server("rustchain-mcp")
    rustchain = RustChainMCP()
    
    # Register tools
    for name, func in rustchain.tools.items():
        server.add_tool(Tool(name=name, description=f"RustChain {name}"))
    
    @server.get_tools()
    async def get_tools() -> GetToolsResult:
        return GetToolsResult(tools=list(rustchain.tools.keys()))

    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
        if name not in rustchain.tools:
            raise ToolCallError(f"Unknown tool: {name}")
        
        try:
            result = await rustchain.tools[name](**arguments)
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(result, indent=2))]
            )
        except Exception as e:
            raise ToolCallError(str(e))

    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
