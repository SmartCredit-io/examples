# SmartCredit.io — Examples

Code examples and integration guides for [SmartCredit.io](https://smartcredit.io) — an AI-driven self-custodial neobank offering fixed-term, fixed-interest DeFi loans, personal fixed income funds, and fixed-rate leveraged Lido staking.

## Platform Overview

SmartCredit.io provides:

- **Borrowing** — collateralized fixed-term, fixed-interest-rate loans with liquidation protection
- **Lending** — personal fixed income funds with stable returns and loss provision safeguards
- **Investing** — fixed-rate leveraged Lido staking for ETH investors
- **Portfolio MCP** — AI chat-based risk/reward portfolio optimization
- **Fiat On/Off-Ramp** — seamless fiat integration

## Developer Integrations

| Integration | Description |
|-------------|-------------|
| Borrow/Lend SDK | Embed borrowing and lending into any wallet or dApp |
| UI Widgets | Drop-in widgets for WordPress and JavaScript environments |
| REST API | Loan requests, collateral management, repayment, and liquidation |

## Examples in This Repo

| Folder | Description |
|--------|-------------|
| `python/` | Python examples for the Aave Liquidation Monitor MCP |

---

## Python — Aave Liquidation Monitor MCP

Python examples showing how to use the [SmartCredit Aave Liquidation Monitor MCP](https://github.com/SmartCredit-io/web3-borrow-lend-mcp) with Claude. The MCP provides real-time liquidation risk intelligence for Aave V3 borrower positions on Ethereum mainnet.

**MCP Endpoint:** `https://mcp.smartcredit.io/web3-borrow-lend-mcp`
**Access:** Public — no API key required

### Prerequisites

```bash
pip install anthropic
```

**Anthropic API key** — used to call Claude models.
Get one at [console.anthropic.com](https://console.anthropic.com).

**Option A — `.env` file (recommended):**

```bash
cp .env.example .env
# then edit .env and fill in your key
```

**Option B — export directly in your shell:**

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

On Windows (PowerShell):

```powershell
$env:ANTHROPIC_API_KEY="sk-ant-..."
```

---

### `python/agents/` — Agent-based examples

These scripts load a `.claude/agents/*.md` definition as the system prompt, keeping
tool instructions and output format in the agent file rather than in code.

| Script | Agent | What it does |
|--------|-------|-------------|
| `liquidation_monitor.py` | `smartcredit-liquidation-monitor.md` | Scannable liquidation risk report — health factor, tier, per-asset thresholds |
| `health_advisor.py` | `smartcredit-health-advisor.md` | Actionable advice to improve health factor and reduce liquidation probability |
| `threshold_finder.py` | `smartcredit-threshold-finder.md` | Per-asset liquidation price thresholds sorted by proximity |
| `stress_tester.py` | `smartcredit-stress-tester.md` | Risk matrix across 7/14/30/90-day horizons with trend interpretation |
| `portfolio_scanner.py` | `smartcredit-portfolio-scanner.md` | Batch scan multiple positions, ranked by liquidation probability |
| `risk_reporter.py` | `smartcredit-risk-reporter.md` | Full written risk report suitable for documentation or team sharing |

```bash
# single address (uses demo address if omitted)
python python/agents/liquidation_monitor.py
python python/agents/liquidation_monitor.py 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045

python python/agents/health_advisor.py 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
python python/agents/threshold_finder.py 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
python python/agents/stress_tester.py 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
python python/agents/stress_tester.py 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 60  # 60-day sigma

python python/agents/risk_reporter.py 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
python python/agents/risk_reporter.py 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 14 60  # 14d horizon, 60d sigma

# portfolio scan — multiple inline addresses
python python/agents/portfolio_scanner.py 0xABC... 0xDEF... 0xGHI...

# portfolio scan — from CSV
python python/agents/portfolio_scanner.py wallets.csv
```

---

### `python/MCP/` — Direct MCP examples

These scripts call the SmartCredit MCP tools directly via a user prompt.

| Script | Tool | What it does |
|--------|------|-------------|
| `liquidation_risk.py` | `get_liquidation_risk` | Direct liquidation risk check for a single address |
| `health_check.py` | `check_api_health` | Ping the MCP server to confirm it is reachable |

```bash
python python/MCP/health_check.py
python python/MCP/liquidation_risk.py
python python/MCP/liquidation_risk.py 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
```

---

### `python/scripts/` — Utilities

| Script | What it does |
|--------|-------------|
| `run_all_examples.py` | Runs every example script sequentially and prints a summary table (status, duration, tokens consumed). Waits 3s between scripts. |

```bash
python python/scripts/run_all_examples.py
```

---

### Shared Helper

`python/smartcredit.py` is imported by all scripts. It configures the Anthropic
client with the SmartCredit MCP server and exposes:

- `run(prompt, system, model, max_tokens)` — calls Claude with MCP tools available

---

### Agent Definitions

`.claude/agents/` contains 6 ready-made agent definitions pulled from the
[web3-borrow-lend-mcp](https://github.com/SmartCredit-io/web3-borrow-lend-mcp/tree/main/.claude/agents)
repo. To refresh them:

```bash
gh api repos/SmartCredit-io/web3-borrow-lend-mcp/contents/.claude/agents | python3 -c "
import json, sys, base64, subprocess
for f in json.load(sys.stdin):
    data = json.loads(subprocess.run(['gh', 'api', f['url']], capture_output=True, text=True).stdout)
    open(f'.claude/agents/{f[\"name\"]}', 'w').write(base64.b64decode(data['content']).decode())
    print('Updated', f['name'])
"
```

---

### Risk Tiers

| Tier | Liquidation Probability | Action |
|---|---|---|
| Safe | 0–5% | No action needed |
| Watch | 5–15% | Monitor closely |
| Warning | 15–35% | Consider reducing exposure |
| Danger | 35–70% | Reduce position urgently |
| Critical | 70–100% | Immediate action required |
| Liquidatable | HF < 1.0 | Position is liquidatable now |

---

## Getting Started

1. Visit [smartcredit.io/learn](https://smartcredit.io/learn) to explore the documentation.
2. Browse examples in this repository by topic.
3. Follow each example's setup instructions.

## Community

- Twitter: [@smartcredit_io](https://twitter.com/smartcredit_io)
- Telegram: [SmartCredit_Community](https://t.me/SmartCredit_Community)

## License

MIT — see [LICENSE](LICENSE).
