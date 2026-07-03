# SmartCredit.io Examples — Claude Context

## Project Purpose

This repository contains code examples for integrating with [SmartCredit.io](https://smartcredit.io), an AI-driven self-custodial neobank built on DeFi. Examples cover the Borrow/Lend SDK, REST API, and UI widgets.

## Platform Summary

- **Product**: Fixed-term, fixed-interest DeFi loans; personal fixed income funds; fixed-rate leveraged Lido staking
- **Users**: ~20,000 registered users
- **Model**: Self-custodial, regulatory-compliant (peer-to-pool-to-peer)
- **Differentiator**: Not a money-market protocol (unlike Aave/Compound) — fixed rates, no bank-run risk

## Developer Surface

- **Borrow/Lend SDK** — JavaScript SDK for embedding loan/lending flows into external wallets and dApps
- **UI Widgets** — prebuilt widgets for WordPress and vanilla JS
- **REST API** — endpoints for auth (challenge-based), loan requests, collateral deposit/withdrawal, repayments, liquidation management, and credit line operations
- **Portfolio MCP** — AI-powered portfolio optimization tool

## Key Conventions for Examples

- Each example lives in its own subfolder with its own `README.md` and runnable entry point
- Use environment variables (never hardcode) for API keys or wallet credentials — document required vars in `.env.example`
- Target the latest stable SDK/API version; note the version in each example's README
- Examples should be minimal and focused — no unnecessary dependencies
- Prefer TypeScript for SDK/API examples; plain JS acceptable for simple widget embeds

## Python — Aave Liquidation Monitor MCP

```
python/MCP/                          Direct MCP examples (call tools via user prompt)
python/agents/                       Agent-based examples (load .md as system prompt)
python/scripts/run_all_examples.py   Runs all examples sequentially
python/scripts/aave_positions/       Aave V3 active positions fetcher (standalone CLI)
python/smartcredit.py                Shared helper — imported by all scripts
.claude/agents/                      6 agent definitions bundled from web3-borrow-lend-mcp repo
requirements.txt                     Single requirements file at repo root
```

### Shared Helper

All scripts import `smartcredit` from `python/smartcredit.py`.
Scripts in `python/agents/` and `python/MCP/` must add this to their `sys.path`:

```python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
```

### Agent Example Pattern

When creating a new agent-based example in `python/agents/`:

1. Load the agent definition from `.claude/agents/<name>.md`
2. Parse frontmatter with `---` split to extract `model`
3. Use the body as the `system` prompt
4. Pass a minimal user message (address and optional params — no API key needed)
5. Call `smartcredit.run(user_message, system=system_prompt, model=model)`

Standard `load_agent()` function to reuse across all agent scripts:

```python
AGENT_MD = os.path.join(
    os.path.dirname(__file__), "..", "..", ".claude", "agents", "<agent-name>.md"
)

def load_agent(path: str) -> tuple[str, str]:
    with open(path) as f:
        content = f.read()
    parts = content.split("---", 2)
    frontmatter = parts[1] if len(parts) >= 3 else ""
    body = parts[2].strip() if len(parts) >= 3 else content.strip()
    m = re.search(r"^model:\s*(.+)$", frontmatter, re.MULTILINE)
    model = m.group(1).strip() if m else "claude-haiku-4-5-20251001"
    return model, body
```

### CSV Helper Pattern

`portfolio_scanner.py` accepts a CSV file with a standard loader:

```python
def load_addresses_from_csv(csv_path: str) -> list[str]:
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        address_col = None
        for candidate in ("address", "wallet", "Address", "Wallet"):
            if candidate in fieldnames:
                address_col = candidate
                break
        addresses = []
        if address_col:
            for row in reader:
                val = row[address_col].strip()
                if val:
                    addresses.append(val)
        else:
            f.seek(0)
            raw_reader = csv.reader(f)
            next(raw_reader, None)
            for row in raw_reader:
                if row and row[0].strip():
                    addresses.append(row[0].strip())
    return addresses
```

### Existing Agent Examples

| Script | Agent | Input |
|--------|-------|-------|
| `liquidation_monitor.py` | `smartcredit-liquidation-monitor.md` | single address |
| `health_advisor.py` | `smartcredit-health-advisor.md` | single address |
| `threshold_finder.py` | `smartcredit-threshold-finder.md` | single address |
| `stress_tester.py` | `smartcredit-stress-tester.md` | single address + optional sigma_window |
| `portfolio_scanner.py` | `smartcredit-portfolio-scanner.md` | multiple addresses or CSV |
| `risk_reporter.py` | `smartcredit-risk-reporter.md` | single address + optional loan_term, sigma_window |

### Running Examples

Always run from the project root:

```bash
# agent examples — single address
python python/agents/liquidation_monitor.py
python python/agents/liquidation_monitor.py 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
python python/agents/health_advisor.py 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
python python/agents/threshold_finder.py 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
python python/agents/stress_tester.py 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
python python/agents/stress_tester.py 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 60
python python/agents/risk_reporter.py 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
python python/agents/risk_reporter.py 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 14 60

# agent examples — portfolio
python python/agents/portfolio_scanner.py wallets.csv
python python/agents/portfolio_scanner.py 0xABC... 0xDEF... 0xGHI...

# MCP direct
python python/MCP/health_check.py
python python/MCP/liquidation_risk.py
python python/MCP/liquidation_risk.py 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
```

### Running All Examples

```bash
python python/scripts/run_all_examples.py
```

---

## Aave V3 Active Positions Fetcher

`python/scripts/aave_positions/` — standalone CLI tool. Scans Ethereum mainnet backwards from the latest block using Etherscan getLogs, validates each borrower via public RPC (`eth_call`), stops when `--limit` active positions found.

### Module layout

```
python/scripts/aave_positions/
  main.py        Entry point — arg parsing, scan loop, export
  config.py      Constants, Web3 setup, Etherscan rate limiter, date_to_block()
  fetcher.py     LogFetcher — Etherscan getLogs pagination, chunk splitting
  validator.py   PositionValidator — calls getUserAccountData, filters by debt/HF
  enricher.py    PositionEnricher — per-asset breakdown (--enrich flag)
  exporter.py    Exporter — writes CSV + JSON with timestamped filenames
  abis/          pool.json, data_provider.json
  output/        Runtime output (gitignored except .gitkeep)
```

### Key constants (config.py)

- `POOL_ADDRESS = 0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2`
- `DATA_PROVIDER_ADDRESS = 0x7B4EB56E7CD4b454BA8ff71E4518426369a138a3`
- `V3_DEPLOY_BLOCK = 16291127`
- `BORROW_TOPIC = Web3.to_hex(w3.keccak(text="Borrow(address,address,address,uint256,uint8,uint256,uint16)"))` — always use `Web3.to_hex()` not `.hex()` to guarantee `0x` prefix

### Etherscan rate limiter

Sliding-window deque of max 3 timestamps — sleeps if 3 calls made within 1 second. All Etherscan calls must go through `etherscan_get()` in `config.py`.

### Output filenames

Named with limit + timestamp: `active_positions_limit{N}_{YYYYMMDD_HHMMSS}.csv/.json`

### Running

```bash
python python/scripts/aave_positions/main.py --limit 10
python python/scripts/aave_positions/main.py --limit 50 --min-debt 10000 --max-hf 1.5
python python/scripts/aave_positions/main.py --limit 10 --enrich --asset USDC
```

### Required env vars

```
ETHERSCAN_API_KEY=   # free tier sufficient
RPC_URL=https://ethereum.publicnode.com   # free public RPC for eth_call
```

---

### Environment Variables

```bash
export ANTHROPIC_API_KEY="..."
```

No SmartCredit API key is needed — the MCP endpoint is public.
Copy `.env.example` to `.env` and fill in your keys. `.env` is in `.gitignore`.
`requirements.txt` is at the repo root — install with `pip install -r requirements.txt`.

### Agent Definitions

`.claude/agents/` files are bundled in this repo and **must not be hand-edited** — they are owned by the upstream [web3-borrow-lend-mcp](https://github.com/SmartCredit-io/web3-borrow-lend-mcp) repo.
To refresh all 6 agent definitions from GitHub:

```bash
gh api repos/SmartCredit-io/web3-borrow-lend-mcp/contents/.claude/agents | python3 -c "
import json, sys, base64, subprocess
for f in json.load(sys.stdin):
    data = json.loads(subprocess.run(['gh', 'api', f['url']], capture_output=True, text=True).stdout)
    open(f'.claude/agents/{f[\"name\"]}', 'w').write(base64.b64decode(data['content']).decode())
    print('Updated', f['name'])
"
```

## Useful Links

- Docs: https://smartcredit.io/learn
- MCP Repo: https://github.com/SmartCredit-io/web3-borrow-lend-mcp
- Twitter: https://twitter.com/smartcredit_io
- Telegram: https://t.me/SmartCredit_Community
