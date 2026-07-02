"""
Run all SmartCredit examples and display a summary table.

Always run from the project root:
    python python/scripts/run_all_examples.py
"""

import os
import subprocess
import sys
import time

DEMO_ADDRESS = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
DEMO_CSV     = "wallets.csv"

TIMEOUT = 120  # seconds per script

# (script_path, args, label)
EXAMPLES = [
    # ── agents: single address ─────────────────────────────────────────────
    ("python/agents/liquidation_monitor.py", [DEMO_ADDRESS],           "liquidation_monitor"),
    ("python/agents/health_advisor.py",      [DEMO_ADDRESS],           "health_advisor"),
    ("python/agents/threshold_finder.py",    [DEMO_ADDRESS],           "threshold_finder"),
    ("python/agents/stress_tester.py",       [DEMO_ADDRESS],           "stress_tester"),
    ("python/agents/risk_reporter.py",       [DEMO_ADDRESS],           "risk_reporter"),
    # ── agents: portfolio (CSV) ────────────────────────────────────────────
    ("python/agents/portfolio_scanner.py",   [DEMO_CSV],               "portfolio_scanner"),
    # ── MCP direct ────────────────────────────────────────────────────────
    ("python/MCP/health_check.py",           [],                        "MCP/health_check"),
    ("python/MCP/liquidation_risk.py",       [DEMO_ADDRESS],           "MCP/liquidation_risk"),
]


def run_example(script: str, args: list) -> dict:
    for arg in args:
        if arg.endswith(".csv") and not os.path.isfile(arg):
            return {
                "status": "SKIP",
                "duration": 0.0,
                "tokens": 0,
                "note": f"missing input file: {arg}",
            }

    cmd = [sys.executable, script] + args
    start = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT)
        duration = time.time() - start
        tokens = _parse_tokens(proc.stderr + proc.stdout)
        if proc.returncode == 0:
            return {
                "status": "PASS",
                "duration": duration,
                "tokens": tokens,
                "note": _first_output_line(proc.stdout),
            }
        else:
            return {
                "status": "FAIL",
                "duration": duration,
                "tokens": tokens,
                "note": _first_output_line(proc.stderr or proc.stdout),
            }
    except subprocess.TimeoutExpired:
        return {
            "status": "TIMEOUT",
            "duration": time.time() - start,
            "tokens": 0,
            "note": f"exceeded {TIMEOUT}s",
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "duration": time.time() - start,
            "tokens": 0,
            "note": str(e)[:80],
        }


def _parse_tokens(text: str) -> int:
    import re

    total = 0
    for m in re.finditer(r"input_tokens=(\d+)\s+output_tokens=(\d+)", text):
        total += int(m.group(1)) + int(m.group(2))
    return total


def _first_output_line(text: str) -> str:
    lines = text.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("Traceback (most recent call last)"):
            for candidate in reversed(lines[i:]):
                c = candidate.strip()
                if c and not c.startswith("File ") and not c.startswith("Traceback"):
                    return c[:80]
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if "[INFO]" in line or "[WARNING]" in line:
            continue
        if "[ERROR]" in line or "[CRITICAL]" in line:
            return line.split("]", 1)[-1].strip()[:80]
        return line[:80]
    return ""


def print_summary(results: list) -> None:
    STATUS_ICON = {"PASS": "✓", "FAIL": "✗", "SKIP": "—", "TIMEOUT": "⏱", "ERROR": "✗"}

    col_label  = max(len(r[0]) for r in results) + 2
    col_status = 10
    col_dur    = 9
    col_tokens = 10
    col_note   = 45
    width      = col_label + col_status + col_dur + col_tokens + col_note

    sep = "─" * width
    print(f"\n{sep}")
    print(f"{'Script':<{col_label}} {'Status':<{col_status}} {'Time':<{col_dur}} {'Tokens':<{col_tokens}} Note")
    print(sep)

    passed = failed = skipped = timed_out = 0
    total_tokens = 0
    for label, res in results:
        icon   = STATUS_ICON.get(res["status"], "?")
        status = f"{icon} {res['status']}"
        dur    = f"{res['duration']:.1f}s" if res["duration"] else "—"
        tokens = f"{res['tokens']:,}" if res.get("tokens") else "—"
        note   = res["note"][:col_note]
        print(f"{label:<{col_label}} {status:<{col_status}} {dur:<{col_dur}} {tokens:<{col_tokens}} {note}")
        total_tokens += res.get("tokens", 0)
        if   res["status"] == "PASS":    passed    += 1
        elif res["status"] == "SKIP":    skipped   += 1
        elif res["status"] == "TIMEOUT": timed_out += 1
        else:                            failed    += 1

    print(sep)
    total = len(results)
    print(f"\n  {passed}/{total} passed  ·  {failed} failed  ·  {timed_out} timed out  ·  {skipped} skipped")
    print(f"  Total tokens consumed: {total_tokens:,}\n")


if __name__ == "__main__":
    total = len(EXAMPLES)
    print(f"\nSmartCredit Examples — running {total} scripts\n")

    results = []
    STATUS_ICON = {"PASS": "✓", "FAIL": "✗", "SKIP": "—", "TIMEOUT": "⏱", "ERROR": "✗"}
    for i, (script, args, label) in enumerate(EXAMPLES, 1):
        print(f"  [{i:2d}/{total}] {label} ...", end="", flush=True)
        res = run_example(script, args)
        icon = STATUS_ICON.get(res["status"], "?")
        dur  = f"  {res['duration']:.1f}s" if res["duration"] else ""
        print(f"  {icon}{dur}")
        results.append((label, res))
        if i < total:
            pause = 30 if res["status"] == "TIMEOUT" else 3
            time.sleep(pause)

    print_summary(results)
