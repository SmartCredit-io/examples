"""
SmartCredit Example: Stress Tester
=====================================
Agent: smartcredit-stress-tester
Source: .claude/agents/smartcredit-stress-tester.md

Stress tests an Aave V3 borrower position across four time horizons
(7, 14, 30, and 90 days) by calling get_liquidation_risk four times.
Shows how liquidation risk evolves over time and interprets the trend.

Usage:
    python python/agents/stress_tester.py [address] [sigma_window]

    address       Borrower wallet address (0x...). Defaults to a demo address.
    sigma_window  Days of price history for volatility estimation (default: 30).

Examples:
    python python/agents/stress_tester.py
    python python/agents/stress_tester.py 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
    python python/agents/stress_tester.py 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 60

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
    "smartcredit-stress-tester.md",
)

DEMO_ADDRESS = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"


def load_agent(path: str) -> tuple[str, str]:
    with open(path) as f:
        content = f.read()
    parts = content.split("---", 2)
    frontmatter = parts[1] if len(parts) >= 3 else ""
    body = parts[2].strip() if len(parts) >= 3 else content.strip()
    m = re.search(r"^model:\s*(.+)$", frontmatter, re.MULTILINE)
    model = m.group(1).strip() if m else "claude-sonnet-4-6"
    return model, body


def stress_test(user_address: str, sigma_window: int = 30) -> str:
    """
    Stress test an Aave V3 position across 7/14/30/90-day horizons.
    Behaviour is driven by the smartcredit-stress-tester.md agent definition.
    """
    log.info(
        "Starting stress test for address=%s sigma_window=%d",
        user_address,
        sigma_window,
    )

    model, system_prompt = load_agent(AGENT_MD)

    user_message = (
        f"Stress test this Aave V3 borrower position across multiple time horizons.\n\n"
        f"Address:      {user_address}\n"
        f"Sigma window: {sigma_window} days"
    )

    log.info("Calling stress test via smartcredit-stress-tester agent (model=%s)", model)
    result = smartcredit.run(user_message, system=system_prompt, model=model, max_tokens=4096)

    if not result:
        log.warning("No text block found in response content")
    else:
        log.info("Stress test complete — report length=%d chars", len(result))

    return result


if __name__ == "__main__":
    address = sys.argv[1] if len(sys.argv) > 1 else DEMO_ADDRESS
    sigma_window = int(sys.argv[2]) if len(sys.argv) > 2 else 30

    log.info("=== Stress Tester starting ===")
    print(f"Stress testing address: {address}")
    print(f"Sigma window:           {sigma_window} days\n")
    print("=" * 60)

    report = stress_test(address, sigma_window)
    print(report)

    log.info("=== Stress Tester done ===")
