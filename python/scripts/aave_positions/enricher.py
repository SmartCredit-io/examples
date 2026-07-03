import json
import os
import time
from typing import Optional

from config import ASSET_FILTER, DATA_PROVIDER_ADDRESS, POOL_ADDRESS, log, w3

_ABI_DIR = os.path.join(os.path.dirname(__file__), "abis")

_ERC20_ABI = [
    {"inputs": [], "name": "symbol",   "outputs": [{"type": "string"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "decimals", "outputs": [{"type": "uint8"}],  "stateMutability": "view", "type": "function"},
]

_ADDRESSES_PROVIDER_ABI = [
    {
        "inputs": [],
        "name": "getPriceOracle",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    }
]

_ORACLE_ABI = [
    {
        "inputs": [{"internalType": "address[]", "name": "assets", "type": "address[]"}],
        "name": "getAssetsPrices",
        "outputs": [{"internalType": "uint256[]", "name": "", "type": "uint256[]"}],
        "stateMutability": "view",
        "type": "function",
    }
]


def _load_abi(name: str) -> list:
    with open(os.path.join(_ABI_DIR, name)) as f:
        return json.load(f)


class PositionEnricher:
    def __init__(self, asset_filter: Optional[str] = ASSET_FILTER):
        self.asset_filter = asset_filter.upper() if asset_filter else None
        self._pool = w3.eth.contract(
            address=w3.to_checksum_address(POOL_ADDRESS),
            abi=_load_abi("pool.json"),
        )
        self._data_provider = w3.eth.contract(
            address=w3.to_checksum_address(DATA_PROVIDER_ADDRESS),
            abi=_load_abi("data_provider.json"),
        )
        self._reserves: list[str] = []
        self._reserve_meta: dict[str, dict] = {}       # lower addr → {symbol, decimals}
        self._prices: dict[str, float] = {}            # lower addr → USD price
        self._variable_rates: dict[str, float] = {}    # lower addr → variable borrow rate (decimal)

    def _init_reserves(self) -> None:
        if self._reserves:
            return

        log.info("fetching reserve list and metadata...")
        self._reserves = self._pool.functions.getReservesList().call()
        log.info("%d reserves found", len(self._reserves))

        # Symbol + decimals (cached — one call per reserve)
        for r in self._reserves:
            try:
                erc20 = w3.eth.contract(address=w3.to_checksum_address(r), abi=_ERC20_ABI)
                symbol = erc20.functions.symbol().call()
                decimals = erc20.functions.decimals().call()
            except Exception:
                symbol, decimals = "?", 18
            self._reserve_meta[r.lower()] = {"symbol": symbol, "decimals": decimals}

        # Variable borrow rates (one call per reserve via DataProvider)
        for r in self._reserves:
            try:
                data = self._data_provider.functions.getReserveData(
                    w3.to_checksum_address(r)
                ).call()
                # index 6 = variableBorrowRate, in ray (1e27)
                self._variable_rates[r.lower()] = data[6] / 1e27
            except Exception:
                self._variable_rates[r.lower()] = 0.0

        # USD prices via Aave price oracle
        try:
            provider_addr = self._pool.functions.ADDRESSES_PROVIDER().call()
            provider = w3.eth.contract(
                address=w3.to_checksum_address(provider_addr),
                abi=_ADDRESSES_PROVIDER_ABI,
            )
            oracle_addr = provider.functions.getPriceOracle().call()
            oracle = w3.eth.contract(
                address=w3.to_checksum_address(oracle_addr),
                abi=_ORACLE_ABI,
            )
            prices_raw = oracle.functions.getAssetsPrices(self._reserves).call()
            for r, price_raw in zip(self._reserves, prices_raw):
                # Aave oracle: USD prices with 8 decimals
                self._prices[r.lower()] = price_raw / 1e8
        except Exception as e:
            log.warning("oracle prices unavailable (%s) — USD amounts will be 0", e)
            for r in self._reserves:
                self._prices[r.lower()] = 0.0

    def enrich(self, positions: dict[str, dict]) -> dict[str, dict]:
        self._init_reserves()
        log.info("enriching %d positions (%d reserves each)...", len(positions), len(self._reserves))

        to_remove: list[str] = []
        total = len(positions)

        for i, (addr, pos) in enumerate(positions.items(), 1):
            if i % 10 == 0 or i == total:
                log.info("enriching %d/%d", i, total)

            borrowed_assets = []
            collateral_assets = []

            for reserve in self._reserves:
                rl = reserve.lower()
                meta = self._reserve_meta.get(rl, {"symbol": "?", "decimals": 18})
                price_usd = self._prices.get(rl, 0.0)
                decimals = meta["decimals"]
                symbol = meta["symbol"]
                factor = 10 ** decimals

                try:
                    ud = self._data_provider.functions.getUserReserveData(
                        w3.to_checksum_address(reserve),
                        w3.to_checksum_address(addr),
                    ).call()
                except Exception:
                    time.sleep(0.02)
                    continue

                (
                    current_a_token_balance,
                    current_stable_debt,
                    current_variable_debt,
                    _principal_stable_debt,
                    _scaled_variable_debt,
                    stable_borrow_rate_ray,
                    _liquidity_rate,
                    _stable_rate_last_updated,
                    usage_as_collateral_enabled,
                ) = ud

                stable_debt = current_stable_debt / factor
                variable_debt = current_variable_debt / factor
                total_debt = stable_debt + variable_debt
                a_balance = current_a_token_balance / factor

                if total_debt > 0:
                    borrow_rate = (
                        stable_borrow_rate_ray / 1e27 if stable_debt > 0
                        else self._variable_rates.get(rl, 0.0)
                    )
                    borrowed_assets.append({
                        "symbol": symbol,
                        "address": reserve,
                        "current_debt": round(total_debt, 6),
                        "current_debt_usd": round(total_debt * price_usd, 2),
                        "stable_rate_debt": round(stable_debt, 6),
                        "variable_rate_debt": round(variable_debt, 6),
                        "borrow_rate": round(borrow_rate, 6),
                    })

                if a_balance > 0:
                    collateral_assets.append({
                        "symbol": symbol,
                        "address": reserve,
                        "balance": round(a_balance, 6),
                        "balance_usd": round(a_balance * price_usd, 2),
                        "usage_as_collateral": usage_as_collateral_enabled,
                    })

                time.sleep(0.02)

            if self.asset_filter:
                if not any(a["symbol"].upper() == self.asset_filter for a in borrowed_assets):
                    to_remove.append(addr)
                    continue

            pos["borrowed_assets"] = borrowed_assets
            pos["collateral_assets"] = collateral_assets

        for addr in to_remove:
            del positions[addr]

        return positions
