"""
SmartCredit Example: Liquidation Risk (Direct MCP)
====================================================
Tool: get_liquidation_risk

Calls the get_liquidation_risk tool directly via a user prompt — no agent
definition file is loaded. The model receives the tool schema from the MCP
server and decides how to call it.

Use cases:
  - "What is the liquidation probability for this Aave position?"
  - "Check health factor and collateral risk for a borrower"
  - Quick risk check without loading an agent system prompt

Setup:
    pip install anthropic
    export ANTHROPIC_API_KEY="your-anthropic-key"

Register the MCP server (one-time, for Claude Code CLI):
    claude mcp add --transport http smartcredit-aave-liquidation-monitor \\
      https://mcp.smartcredit.io/web3-borrow-lend-mcp
"""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import smartcredit

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def check_liquidation_risk(user_address: str, loan_term: int = 7) -> str:
    """
    Check liquidation risk for an Aave V3 borrower position.

    Uses the get_liquidation_risk tool to return:
      - Health factor
      - Liquidation probability over the given loan term
      - Risk tier (Safe / Watch / Warning / Danger / Critical / Liquidatable)
      - Per-asset collateral and liquidation price thresholds
    """
    log.info(
        "Starting liquidation risk check — address=%s loan_term=%d",
        user_address,
        loan_term,
    )

    prompt = (
        f"Use the get_liquidation_risk tool to assess this Aave V3 borrower position.\n\n"
        f"Address:   {user_address}\n"
        f"Loan term: {loan_term} days\n\n"
        f"Return: health factor, liquidation probability, risk tier, "
        f"per-asset liquidation prices, and a plain-English risk summary."
    )

    log.info("Calling get_liquidation_risk via SmartCredit MCP")
    result = smartcredit.run(prompt)

    if not result:
        log.warning("No text block found in response content")
    else:
        log.info("Risk check complete — report length=%d chars", len(result))

    return result


if __name__ == "__main__":
    address = sys.argv[1] if len(sys.argv) > 1 else "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    loan_term = int(sys.argv[2]) if len(sys.argv) > 2 else 7

    log.info("=== Liquidation Risk Checker starting ===")
    print(f"Checking address: {address}")
    print(f"Loan term:        {loan_term} days")
    print("=" * 60)

    report = check_liquidation_risk(address, loan_term)
    print(report)

    log.info("=== Liquidation Risk Checker done ===")
