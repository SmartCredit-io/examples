"""
SmartCredit shared helper — reused by all example scripts.

Sets up the Anthropic client with the SmartCredit Aave Liquidation Monitor MCP
and exposes a single `run(prompt)` function that calls Claude with the MCP tools
available. No API key is required — the SmartCredit MCP is a public endpoint.
"""

import os
import logging
import anthropic

log = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
SMARTCREDIT_MCP_URL = os.environ.get(
    "SMARTCREDIT_MCP_URL",
    "https://mcp.smartcredit.io/web3-borrow-lend-mcp",
)

MCP_SERVER = {
    "type": "url",
    "url": SMARTCREDIT_MCP_URL,
    "name": "smartcredit-aave-liquidation-monitor",
}

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def run(
    prompt: str,
    system: str = None,
    model: str = "claude-haiku-4-5-20251001",
    max_tokens: int = 4096,
) -> str:
    """
    Send a prompt to Claude with the SmartCredit MCP tools available.
    Claude will call the appropriate tools and return a final answer.
    Pass system to override the default behaviour with an agent definition.
    """
    kwargs = {"system": system} if system else {}
    response = client.beta.messages.create(
        model=model,
        max_tokens=max_tokens,
        mcp_servers=[MCP_SERVER],
        messages=[{"role": "user", "content": prompt}],
        betas=["mcp-client-2025-04-04"],
        **kwargs,
    )
    log.info(
        "Response received — stop_reason=%s input_tokens=%d output_tokens=%d",
        response.stop_reason,
        response.usage.input_tokens,
        response.usage.output_tokens,
    )
    result = ""
    for b in response.content:
        if b.type == "text":
            result = result + "\n\n" + b.text
    return result
