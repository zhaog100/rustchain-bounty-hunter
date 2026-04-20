# RustChain MCP Server

Connect any AI agent to RustChain via Model Context Protocol (MCP).

## Install

```bash
pip install rustchain-mcp
```

## Usage with Claude Code

Add to your `.cursor/rules` or Claude Code config:

```json
{
  "mcpServers": {
    "rustchain": {
      "command": "python",
      "args": ["-m", "rustchain_mcp.mcp_server"]
    }
  }
}
```

## Tools Available

- `rustchain_health` - Check node status
- `rustchain_balance` - Get wallet balance  
- `rustchain_miners` - List active miners
- `rustchain_epoch` - Current epoch info
- `rustchain_create_wallet` - Register new wallet
- `rustchain_submit_attestation` - Submit hardware proof
- `rustchain_bounties` - List open bounties

## Configuration

Set `RUSTCHAIN_NODE_URL` environment variable to override default (`https://rustchain.org`).

## Bounty

Built for [RustChain Bounty #2859](https://github.com/Scottcjn/rustchain-bounties/issues/2859) (25 RTC).
