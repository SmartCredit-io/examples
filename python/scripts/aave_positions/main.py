#!/usr/bin/env python3
"""Aave V3 Ethereum — Active Borrow Positions Fetcher
Scans backwards from the latest block, validating positions on the fly,
and stops as soon as --limit active positions are found.
"""

import argparse
import logging
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from config import ASSET_FILTER, MAX_HF, MIN_DEBT_USD, V3_DEPLOY_BLOCK, log, w3
from enricher import PositionEnricher
from exporter import Exporter
from fetcher import LogFetcher
from validator import PositionValidator


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Aave V3 — scan backwards from latest block for active borrow positions",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--end-block",  type=int,   help="Block to start scanning backwards from (default: latest)")
    p.add_argument("--floor-block", type=int,  default=V3_DEPLOY_BLOCK,
                   help="Oldest block to consider (default: V3 deploy block)")
    p.add_argument("--chunk-size", type=int,   help="Blocks per Etherscan getLogs call")
    p.add_argument("--min-debt",   type=float, help="Minimum debt in USD")
    p.add_argument("--max-hf",     type=float, help="Maximum health factor")
    p.add_argument("--asset",      metavar="SYMBOL", help="Filter by borrowed asset symbol (requires --enrich)")
    p.add_argument("--enrich",     action="store_true", help="Fetch per-asset breakdown for each position")
    p.add_argument("--output-dir", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "output"),
                   help="Directory for output files")
    p.add_argument("--csv",        metavar="PATH", help="CSV output file path")
    p.add_argument("--limit",      type=int,   default=100,
                   help="Stop after finding this many active positions")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%H:%M:%S",
    )

    end_block   = args.end_block or w3.eth.block_number
    floor_block = args.floor_block
    chunk_size  = args.chunk_size or config.BLOCK_CHUNK_SIZE
    min_debt    = args.min_debt   if args.min_debt  is not None else MIN_DEBT_USD
    max_hf      = args.max_hf    if args.max_hf    is not None else MAX_HF
    asset_filter = args.asset or ASSET_FILTER
    limit       = args.limit

    print("=" * 60)
    print("  Aave V3 Active Borrow Positions Fetcher")
    print("=" * 60)
    print(f"  Direction:    backwards from block {end_block:,}")
    print(f"  Floor block:  {floor_block:,}")
    print(f"  Chunk size:   {chunk_size:,} blocks")
    print(f"  Limit:        {limit:,} active positions")
    print(f"  Min debt USD: {min_debt}")
    print(f"  Max HF:       {max_hf}")
    if asset_filter:
        print(f"  Asset filter: {asset_filter}")
    print("─" * 60)

    fetcher   = LogFetcher(chunk_size=chunk_size)
    validator = PositionValidator(min_debt_usd=min_debt, max_hf=max_hf)

    positions: dict[str, dict] = {}
    seen: set[str] = set()
    current = end_block
    chunks_scanned = 0
    addresses_checked = 0

    while len(positions) < limit and current >= floor_block:
        chunk_start = max(current - chunk_size + 1, floor_block)

        log.info(
            "chunk %d→%d | %d/%d active found | %d unique addresses checked",
            chunk_start, current, len(positions), limit, addresses_checked,
        )

        new_addrs = [a for a in fetcher.fetch_chunk(chunk_start, current) if a not in seen]
        seen.update(new_addrs)

        if new_addrs:
            log.info("  %d new borrower addresses in chunk", len(new_addrs))

        for addr in new_addrs:
            addresses_checked += 1
            pos = validator.validate_one(addr)
            if pos:
                positions[addr] = pos
                log.info(
                    "  ACTIVE [%d/%d]  %s  HF=%.3f  debt=$%s",
                    len(positions), limit, addr, pos["health_factor"],
                    f"{pos['total_debt_usd']:,.0f}",
                )
                if len(positions) >= limit:
                    break

        chunks_scanned += 1
        current = chunk_start - 1

    if len(positions) >= limit:
        log.info("limit of %d reached after scanning %d chunks", limit, chunks_scanned)
    else:
        log.info("scan complete (floor block reached) — found %d active positions", len(positions))

    # Optional enrichment
    if args.enrich and positions:
        enricher = PositionEnricher(asset_filter=asset_filter)
        positions = enricher.enrich(positions)
        log.info("after enrichment/asset filter: %d positions", len(positions))

    # Export
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem  = f"active_positions_limit{limit}_{stamp}"
    csv_path  = args.csv or os.path.join(args.output_dir, f"{stem}.csv")
    json_path = os.path.join(args.output_dir, f"{stem}.json")
    exporter = Exporter(output_dir=args.output_dir, csv_path=csv_path, json_path=json_path)
    csv_out  = exporter.save_csv(positions)
    json_out = exporter.save_json(positions)

    print("\n" + "=" * 60)
    print(f"  ACTIVE POSITIONS FOUND: {len(positions):,}")
    print(f"  Chunks scanned:         {chunks_scanned:,}")
    print(f"  Addresses checked:      {addresses_checked:,}")
    print("─" * 60)
    print(f"  Saved: {csv_out}")
    print(f"  Saved: {json_out}")
    print("=" * 60)


if __name__ == "__main__":
    main()
