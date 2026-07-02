"""
SmartCredit Example: API Health Check (Direct MCP)
====================================================
Tool: check_api_health

Pings the SmartCredit MCP server to confirm it is reachable. Useful as a
first step to verify your MCP connection before running other examples.

Setup:
    pip install anthropic
    export ANTHROPIC_API_KEY="your-anthropic-key"
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


def ping_server() -> str:
    """
    Ping the SmartCredit MCP server using the check_api_health tool.
    Returns "ok" on success or an error description.
    """
    log.info("Pinging SmartCredit MCP server")

    prompt = (
        "Use the check_api_health tool to verify that the SmartCredit "
        "Aave Liquidation Monitor MCP server is reachable. Report the result."
    )

    result = smartcredit.run(prompt)

    if not result:
        log.warning("No response received from health check")
    else:
        log.info("Health check complete")

    return result


if __name__ == "__main__":
    log.info("=== API Health Check starting ===")
    print("Pinging SmartCredit MCP server...")
    print("=" * 60)

    result = ping_server()
    print(result)

    log.info("=== API Health Check done ===")
