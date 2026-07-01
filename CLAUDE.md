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

## Useful Links

- Docs: https://smartcredit.io/learn
- Twitter: https://twitter.com/smartcredit_io
- Telegram: https://t.me/SmartCredit_Community
