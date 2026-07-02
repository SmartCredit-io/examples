"""
SmartCredit Example: Liquidation Monitor
==========================================
Agent: smartcredit-liquidation-monitor
Source: .claude/agents/smartcredit-liquidation-monitor.md

Uses the agent definition .md file as the system prompt so that output
format, tier badges, and edge-case handling live in the .md — not in code.

Returns a scannable liquidation risk report for any Aave V3 borrower position.

Usage:
    python python/agents/liquidation_monitor.py [address]

    address  Borrower wallet address (0x...). Defaults to a demo address.

Examples:
    python python/agents/liquidation_monitor.py
    python python/agents/liquidation_monitor.py 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045

Setup:
    pip install anthropic
    export ANTHROPIC_API_KEY="your-anthropic-key"
"""

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
    "smartcredit-liquidation-monitor.md",
)

DEMO_ADDRESS = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"


def load_agent(path: str) -> tuple[str, str]:
    """Parse the agent .md file and return (model, system_prompt)."""
    with open(path) as f:
        content = f.read()
    parts = content.split("---", 2)
    frontmatter = parts[1] if len(parts) >= 3 else ""
    body = parts[2].strip() if len(parts) >= 3 else content.strip()
    m = re.search(r"^model:\s*(.+)$", frontmatter, re.MULTILINE)
    model = m.group(1).strip() if m else "claude-haiku-4-5-20251001"
    return model, body


def check_liquidation_risk(user_address: str) -> str:
    """
    Return a liquidation risk report for an Aave V3 borrower position.
    Behaviour is driven by the smartcredit-liquidation-monitor.md agent definition.
    """
    log.info("Starting liquidation monitor for address=%s", user_address)

    model, system_prompt = load_agent(AGENT_MD)

    user_message = (
        f"Check the liquidation risk for this Aave V3 borrower position.\n\n"
        f"Address: {user_address}"
    )

    log.info("Calling get_liquidation_risk via smartcredit-liquidation-monitor agent (model=%s)", model)
    result = smartcredit.run(user_message, system=system_prompt, model=model)

    if not result:
        log.warning("No text block found in response content")
    else:
        log.info("Liquidation monitor complete — report length=%d chars", len(result))

    return result


if __name__ == "__main__":
    address = sys.argv[1] if len(sys.argv) > 1 else DEMO_ADDRESS

    log.info("=== Liquidation Monitor starting ===")
    print(f"Checking address: {address}\n")
    print("=" * 60)

    report = check_liquidation_risk(address)
    print(report)

    log.info("=== Liquidation Monitor done ===")
