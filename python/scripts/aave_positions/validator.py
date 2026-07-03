import json
import os
import time
from typing import Optional

from config import MAX_HF, MIN_DEBT_USD, POOL_ADDRESS, log, w3

_ABI_DIR = os.path.join(os.path.dirname(__file__), "abis")
_MAX_UINT256 = 2**256 - 1


def _load_abi(name: str) -> list:
    with open(os.path.join(_ABI_DIR, name)) as f:
        return json.load(f)


class PositionValidator:
    def __init__(
        self,
        min_debt_usd: float = MIN_DEBT_USD,
        max_hf: float = MAX_HF,
    ):
        self.min_debt_usd = min_debt_usd
        self.max_hf = max_hf
        self._pool = w3.eth.contract(
            address=w3.to_checksum_address(POOL_ADDRESS),
            abi=_load_abi("pool.json"),
        )

    def validate_one(self, addr: str) -> Optional[dict]:
        """Call getUserAccountData for one address. Returns position dict if active, else None."""
        try:
            result = self._pool.functions.getUserAccountData(
                w3.to_checksum_address(addr)
            ).call()
        except Exception as e:
            log.warning("getUserAccountData failed for %s: %s", addr, e)
            time.sleep(0.05)
            return None

        (
            total_collateral_base,
            total_debt_base,
            available_borrows_base,
            current_liquidation_threshold,
            ltv,
            health_factor_raw,
        ) = result

        if total_debt_base == 0:
            time.sleep(0.05)
            return None

        total_debt_usd = total_debt_base / 1e8
        hf = 999.0 if health_factor_raw == _MAX_UINT256 else health_factor_raw / 1e18

        if total_debt_usd < self.min_debt_usd:
            time.sleep(0.05)
            return None
        if hf > self.max_hf:
            time.sleep(0.05)
            return None

        time.sleep(0.05)
        return {
            "total_collateral_usd": round(total_collateral_base / 1e8, 2),
            "total_debt_usd": round(total_debt_usd, 2),
            "available_borrow_usd": round(available_borrows_base / 1e8, 2),
            "liquidation_threshold": round(current_liquidation_threshold / 1e4, 4),
            "ltv": round(ltv / 1e4, 4),
            "health_factor": round(min(hf, 999.0), 4),
        }
