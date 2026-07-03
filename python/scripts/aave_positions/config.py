import logging
import os
import sys
import time
from collections import deque
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv
from web3 import Web3

log = logging.getLogger("aave_positions")

load_dotenv()

POOL_ADDRESS = "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2"
DATA_PROVIDER_ADDRESS = "0x7B4EB56E7CD4b454BA8ff71E4518426369a138a3"
V3_DEPLOY_BLOCK = 16291127

RPC_URL = os.getenv("RPC_URL", "")
BLOCK_CHUNK_SIZE = int(os.getenv("BLOCK_CHUNK_SIZE", "2000"))
START_DATE_ENV = os.getenv("START_DATE", "")
START_BLOCK_ENV = int(os.getenv("START_BLOCK", str(V3_DEPLOY_BLOCK)))
END_BLOCK_ENV = os.getenv("END_BLOCK", "latest")
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY", "")
MIN_DEBT_USD = float(os.getenv("MIN_DEBT_USD", "0"))
MAX_HF = float(os.getenv("MAX_HF", "999"))
ASSET_FILTER = os.getenv("ASSET_FILTER", "").strip() or None

if not RPC_URL:
    sys.exit("ERROR: RPC_URL not set. Copy .env.example to .env and fill in your key.")

w3 = Web3(Web3.HTTPProvider(RPC_URL))
if not w3.is_connected():
    sys.exit(f"ERROR: Cannot connect to RPC endpoint: {RPC_URL}")

BORROW_TOPIC = Web3.to_hex(w3.keccak(text="Borrow(address,address,address,uint256,uint8,uint256,uint16)"))
REPAY_TOPIC = Web3.to_hex(w3.keccak(text="Repay(address,address,address,uint256,bool)"))

# Sliding-window rate limiter: max 3 Etherscan calls per second.
# Tracks the last 3 call timestamps; sleeps when the window is full.
_etherscan_timestamps: deque = deque(maxlen=3)


def etherscan_get(url: str, timeout: int = 30, retries: int = 5) -> requests.Response:
    for attempt in range(retries):
        if len(_etherscan_timestamps) == 3:
            wait = 1.0 - (time.monotonic() - _etherscan_timestamps[0])
            if wait > 0:
                time.sleep(wait)
        _etherscan_timestamps.append(time.monotonic())
        try:
            return requests.get(url, timeout=timeout)
        except requests.exceptions.Timeout:
            wait = min(2 ** attempt, 60)
            log.warning("Etherscan request timed out (attempt %d/%d) — retrying in %.0fs", attempt + 1, retries, wait)
            time.sleep(wait)
        except requests.exceptions.RequestException as e:
            wait = min(2 ** attempt, 60)
            log.warning("Etherscan request error (attempt %d/%d): %s — retrying in %.0fs", attempt + 1, retries, e, wait)
            time.sleep(wait)
    raise RuntimeError(f"Etherscan request failed after {retries} attempts: {url}")


def date_to_block(date_str: str) -> int:
    """Convert YYYY-MM-DD to the nearest Ethereum block at or after midnight UTC.
    Primary: Etherscan API. Fallback: binary search (~20 RPC calls)."""
    ts = int(datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())

    if ETHERSCAN_API_KEY:
        try:
            url = (
                "https://api.etherscan.io/v2/api"
                f"?chainid=1&module=block&action=getblocknobytime"
                f"&timestamp={ts}&closest=after&apikey={ETHERSCAN_API_KEY}"
            )
            resp = etherscan_get(url).json()
            result = resp.get("result")
            if result and str(result).isdigit():
                log.info("date→block via Etherscan: %s → block %s", date_str, result)
                return int(result)
            log.warning("Etherscan returned unexpected result (%s) — falling back to binary search", result)
        except Exception as e:
            log.warning("Etherscan request failed (%s) — falling back to binary search", e)
    else:
        log.info("ETHERSCAN_API_KEY not set — using binary search for date→block (~20 RPC calls)")
    lo, hi = V3_DEPLOY_BLOCK, w3.eth.block_number
    while lo < hi:
        mid = (lo + hi) // 2
        if w3.eth.get_block(mid)["timestamp"] < ts:
            lo = mid + 1
        else:
            hi = mid
    return lo
