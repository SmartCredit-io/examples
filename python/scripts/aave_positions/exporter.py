import csv
import json
import os


class Exporter:
    def __init__(self, output_dir: str, csv_path: str | None = None, json_path: str | None = None):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.csv_path  = csv_path  or os.path.join(output_dir, "active_positions.csv")
        self.json_path = json_path or os.path.join(output_dir, "active_positions.json")

    def save_csv(self, positions: dict[str, dict]) -> str:
        if not positions:
            return self.csv_path

        enriched = any("borrowed_assets" in p for p in positions.values())

        base_fields = [
            "address",
            "health_factor",
            "total_debt_usd",
            "total_collateral_usd",
            "ltv",
            "available_borrow_usd",
        ]
        fieldnames = base_fields + (["borrowed_assets", "collateral_assets"] if enriched else [])

        # Ensure the CSV output directory exists
        os.makedirs(os.path.dirname(os.path.abspath(self.csv_path)), exist_ok=True)

        with open(self.csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for addr, pos in positions.items():
                row: dict = {
                    "address": addr,
                    "health_factor": pos.get("health_factor"),
                    "total_debt_usd": pos.get("total_debt_usd"),
                    "total_collateral_usd": pos.get("total_collateral_usd"),
                    "ltv": pos.get("ltv"),
                    "available_borrow_usd": pos.get("available_borrow_usd"),
                }
                if enriched:
                    row["borrowed_assets"] = "|".join(
                        f"{a['symbol']}:{a['current_debt_usd']}"
                        for a in pos.get("borrowed_assets", [])
                    )
                    row["collateral_assets"] = "|".join(
                        f"{a['symbol']}:{a['balance_usd']}"
                        for a in pos.get("collateral_assets", [])
                    )
                writer.writerow(row)

        return self.csv_path

    def save_json(self, positions: dict[str, dict]) -> str:
        records = [{"address": addr, **pos} for addr, pos in positions.items()]
        with open(self.json_path, "w") as f:
            json.dump(records, f, indent=2)
        return self.json_path
