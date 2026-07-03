import json

from config import (
    BLOCK_CHUNK_SIZE,
    BORROW_TOPIC,
    ETHERSCAN_API_KEY,
    POOL_ADDRESS,
    etherscan_get,
    log,
)

_ETHERSCAN_LOGS_URL = (
    "https://api.etherscan.io/v2/api"
    "?chainid=1&module=logs&action=getLogs"
)


class LogFetcher:
    def __init__(self, chunk_size: int = BLOCK_CHUNK_SIZE):
        self.chunk_size = chunk_size

    def fetch_chunk(self, from_block: int, to_block: int) -> list[str]:
        """Return unique borrower addresses from Borrow events in [from_block, to_block]."""
        return list(set(self._fetch_etherscan(BORROW_TOPIC, from_block, to_block)))

    def _fetch_etherscan(self, topic: str, from_block: int, to_block: int) -> list[str]:
        addresses: list[str] = []
        page = 1

        while True:
            url = (
                f"{_ETHERSCAN_LOGS_URL}"
                f"&address={POOL_ADDRESS}"
                f"&topic0={topic}"
                f"&fromBlock={from_block}&toBlock={to_block}"
                f"&page={page}&offset=1000"
                f"&apikey={ETHERSCAN_API_KEY}"
            )
            resp = etherscan_get(url).json()
            status = resp.get("status")
            result = resp.get("result", [])
            message = resp.get("message", "")

            if status != "1":
                if isinstance(result, list) and len(result) == 0:
                    break
                if "no records found" in message.lower():
                    break
                err = str(result).lower()
                if any(x in err for x in ("too large", "limit", "exceed", "range")):
                    mid = (from_block + to_block) // 2
                    if mid == from_block:
                        log.warning("single-block range failed, skipping block %d", from_block)
                        break
                    log.warning("block range too large (%d blocks) — splitting", to_block - from_block + 1)
                    addresses += self._fetch_etherscan(topic, from_block, mid)
                    addresses += self._fetch_etherscan(topic, mid + 1, to_block)
                    return addresses
                log.error("Etherscan getLogs error (blocks %d-%d): %s / %s", from_block, to_block, message, result)
                break

            for entry in result:
                topics = entry.get("topics", [])
                # topics[2] = onBehalfOf (the actual borrower, not msg.sender)
                if len(topics) >= 3:
                    addresses.append(("0x" + topics[2][-40:]).lower())

            if len(result) < 1000:
                break
            page += 1

        return addresses
