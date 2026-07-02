"""
SmartCredit Example: Threshold Finder
=======================================
Agent: smartcredit-threshold-finder
Source: .claude/agents/smartcredit-threshold-finder.md

Extracts and presents all per-asset liquidation price thresholds for an
Aave V3 position. Tells the user exactly what price drop triggers
liquidation for each collateral asset they hold.

Usage:
    python python/agents/threshold_finder.py [address]

    address  Borrower wallet address (0x...). Defaults to a demo address.

Examples:
    python python/agents/threshold_finder.py
    python python/agents/threshold_finder.py 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045

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
    "smartcredit-threshold-finder.md",
)

DEMO_ADDRESS = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"


def load_agent(path: str) -> tuple[str, str]:
    with open(path) as f:
        content = f.read()
    parts = content.split("---", 2)
    frontmatter = parts[1] if len(parts) >= 3 else ""
    body = parts[2].strip() if len(parts) >= 3 else content.strip()
    m = re.search(r"^model:\s*(.+)$", frontmatter, re.MULTILINE)
    model = m.group(1).strip() if m else "claude-haiku-4-5-20251001"
    return model, body


def find_thresholds(user_address: str) -> str:
    """
    Return per-asset liquidation price thresholds for an Aave V3 position.
    Behaviour is driven by the smartcredit-threshold-finder.md agent definition.
    """
    log.info("Starting threshold finder for address=%s", user_address)

    model, system_prompt = load_agent(AGENT_MD)

    user_message = (
        f"Find the liquidation price thresholds for this Aave V3 position.\n\n"
        f"Address: {user_address}"
    )

    log.info("Calling get_liquidation_risk via smartcredit-threshold-finder agent (model=%s)", model)
    result = smartcredit.run(user_message, system=system_prompt, model=model)

    if not result:
        log.warning("No text block found in response content")
    else:
        log.info("Threshold finder complete — report length=%d chars", len(result))

    return result


if __name__ == "__main__":
    address = sys.argv[1] if len(sys.argv) > 1 else DEMO_ADDRESS

    log.info("=== Threshold Finder starting ===")
    print(f"Finding thresholds for: {address}\n")
    print("=" * 60)

    report = find_thresholds(address)
    print(report)

    log.info("=== Threshold Finder done ===")
