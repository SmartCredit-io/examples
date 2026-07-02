"""
SmartCredit Example: Portfolio Scanner
========================================
Agent: smartcredit-portfolio-scanner
Source: .claude/agents/smartcredit-portfolio-scanner.md

Scans multiple Aave V3 borrower positions and produces a portfolio-level
risk summary ranked by liquidation probability. Accepts a list of addresses
as CLI arguments or a CSV file.

Usage — multiple addresses:
    python python/agents/portfolio_scanner.py <address1> <address2> [address3 ...]

Usage — CSV file:
    python python/agents/portfolio_scanner.py <csv_file>

    csv_file  Path to a CSV file. Any column named 'address' or 'wallet'
              (case-insensitive) is used. Falls back to first column.

Examples:
    python python/agents/portfolio_scanner.py                             # demo (3 hardcoded)
    python python/agents/portfolio_scanner.py wallets.csv                 # from CSV
    python python/agents/portfolio_scanner.py 0xABC... 0xDEF... 0xGHI...  # inline list

Setup:
    pip install anthropic
    export ANTHROPIC_API_KEY="your-anthropic-key"
"""

import csv
import logging
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import smartcredit

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

AGENT_MD = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    ".claude",
    "agents",
    "smartcredit-portfolio-scanner.md",
)

DEMO_ADDRESSES = [
    "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
    "0xae2Fc483527B8EF99EB5D9B44875F005ba1FaE13",
    "0x176F3DAb24a159341c0509bB36B833E7fdd0a132",
]


def load_agent(path: str) -> tuple[str, str]:
    with open(path) as f:
        content = f.read()
    parts = content.split("---", 2)
    frontmatter = parts[1] if len(parts) >= 3 else ""
    body = parts[2].strip() if len(parts) >= 3 else content.strip()
    m = re.search(r"^model:\s*(.+)$", frontmatter, re.MULTILINE)
    model = m.group(1).strip() if m else "claude-sonnet-4-6"
    return model, body


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
            header = next(raw_reader, None)
            log.warning(
                "No 'address'/'wallet' column found. Using first column: %s",
                header[0] if header else "(none)",
            )
            for row in raw_reader:
                if row and row[0].strip():
                    addresses.append(row[0].strip())
    return addresses


def scan_portfolio(addresses: list[str]) -> str:
    """
    Scan multiple Aave V3 positions and rank by liquidation probability.
    Behaviour is driven by the smartcredit-portfolio-scanner.md agent definition.
    """
    log.info("Starting portfolio scan — %d address(es)", len(addresses))

    model, system_prompt = load_agent(AGENT_MD)

    address_list = "\n".join(f"- {addr}" for addr in addresses)
    user_message = (
        f"Scan these Aave V3 borrower positions and rank them by liquidation risk.\n\n"
        f"Addresses ({len(addresses)} total):\n{address_list}"
    )

    log.info("Calling portfolio scanner (model=%s)", model)
    result = smartcredit.run(
        user_message, system=system_prompt, model=model, max_tokens=8192
    )

    if not result:
        log.warning("No text block found in response content")
    else:
        log.info("Portfolio scan complete — report length=%d chars", len(result))

    return result


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        arg = sys.argv[1]
        if os.path.isfile(arg):
            addresses = load_addresses_from_csv(arg)
            log.info("=== Portfolio Scanner starting (CSV: %d addresses) ===", len(addresses))
            print(f"Scanning positions from: {arg}")
        else:
            addresses = sys.argv[1:]
            log.info("=== Portfolio Scanner starting (%d inline addresses) ===", len(addresses))
            print(f"Scanning {len(addresses)} inline address(es)")
    else:
        addresses = DEMO_ADDRESSES
        log.info("=== Portfolio Scanner starting (demo: %d addresses) ===", len(addresses))
        print(f"Scanning demo portfolio ({len(addresses)} addresses)")

    print("=" * 60)

    report = scan_portfolio(addresses)
    print(report)

    log.info("=== Portfolio Scanner done ===")
