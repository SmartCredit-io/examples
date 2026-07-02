"""
SmartCredit Example: Risk Reporter
=====================================
Agent: smartcredit-risk-reporter
Source: .claude/agents/smartcredit-risk-reporter.md

Generates a full, structured liquidation risk report for an Aave V3
borrower position. The report is written in professional language suitable
for sharing with a team or saving as documentation.

Usage:
    python python/agents/risk_reporter.py [address] [loan_term] [sigma_window]

    address       Borrower wallet address (0x...). Defaults to a demo address.
    loan_term     Forecast horizon in days (default: 7).
    sigma_window  Days of price history for volatility estimation (default: 30).

Examples:
    python python/agents/risk_reporter.py
    python python/agents/risk_reporter.py 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
    python python/agents/risk_reporter.py 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 14 60

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
    "smartcredit-risk-reporter.md",
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


def generate_report(
    user_address: str, loan_term: int = 7, sigma_window: int = 30
) -> str:
    """
    Generate a full risk report for an Aave V3 borrower position.
    Behaviour is driven by the smartcredit-risk-reporter.md agent definition.
    """
    log.info(
        "Starting risk reporter for address=%s loan_term=%d sigma_window=%d",
        user_address,
        loan_term,
        sigma_window,
    )

    model, system_prompt = load_agent(AGENT_MD)

    user_message = (
        f"Generate a full risk report for this Aave V3 borrower position.\n\n"
        f"Address:      {user_address}\n"
        f"Loan term:    {loan_term} days\n"
        f"Sigma window: {sigma_window} days"
    )

    log.info("Calling risk reporter agent (model=%s)", model)
    result = smartcredit.run(
        user_message, system=system_prompt, model=model, max_tokens=8192
    )

    if not result:
        log.warning("No text block found in response content")
    else:
        log.info("Risk report complete — report length=%d chars", len(result))

    return result


if __name__ == "__main__":
    address = sys.argv[1] if len(sys.argv) > 1 else DEMO_ADDRESS
    loan_term = int(sys.argv[2]) if len(sys.argv) > 2 else 7
    sigma_window = int(sys.argv[3]) if len(sys.argv) > 3 else 30

    log.info("=== Risk Reporter starting ===")
    print(f"Generating report for: {address}")
    print(f"Loan term:             {loan_term} days")
    print(f"Sigma window:          {sigma_window} days\n")
    print("=" * 60)

    report = generate_report(address, loan_term, sigma_window)
    print(report)

    log.info("=== Risk Reporter done ===")
