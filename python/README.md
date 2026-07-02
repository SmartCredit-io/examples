# SmartCredit Python Examples

Python examples for the [SmartCredit Aave Liquidation Monitor MCP](https://github.com/SmartCredit-io/web3-borrow-lend-mcp) — 6 AI agents for real-time Aave V3 liquidation risk intelligence.

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-anthropic-key"
```

No SmartCredit API key is required — the MCP server is a public endpoint.

## MCP Server

All examples connect to:
```
https://mcp.smartcredit.io/web3-borrow-lend-mcp
```

Register it once in Claude Code CLI:
```bash
claude mcp add --transport http smartcredit-aave-liquidation-monitor \
  https://mcp.smartcredit.io/web3-borrow-lend-mcp
```

## Agent Groups

| Folder | Agents | What it does |
|--------|--------|--------------|
| `agents/` | liquidation-monitor, health-advisor, threshold-finder | Fast single-address lookups (Haiku) |
| `agents/` | stress-tester, portfolio-scanner, risk-reporter | Multi-call reasoning and written output (Sonnet) |

## Underlying MCP Tools

All agents are built on 2 tools:

- `get_liquidation_risk` — Health factor, liquidation probability, per-asset thresholds
- `check_api_health` — Server reachability ping
