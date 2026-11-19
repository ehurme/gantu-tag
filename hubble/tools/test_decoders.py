"""Cross-check the Python decoder against payloads packed by the C core (make -C hubble/firmware/test run)."""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gantu_payload import decode, pack, unpack  # noqa: E402

path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "../firmware/test/payloads.csv")
fails, n, prev = 0, 0, None
with open(path, newline="") as f:
    for r in csv.DictReader(f):
        n += 1
        b = bytes.fromhex(r["hex"])
        d = decode(b)
        checks = [
            pack(unpack(b)) == b,
            d["alive"] == (r["alive"] == "1"),
            d["vedba_cum_counts"] == int(r["vedba_units"]),
            abs(d["temp_c"] - int(r["t_cc"]) / 100) <= 0.125 + 1e-9,
            abs(d["pressure_hpa"] - int(r["p_pa"]) / 100) <= 0.05 + 1e-9,
            abs(d["battery_v"] - int(r["batt_mv"]) / 1000) <= 0.025 + 1e-9,
            prev is None or d["counter"] == (prev + 1) % 256,
        ]
        if not all(checks):
            fails += 1
            print("mismatch", r["hex"], checks)
        prev = d["counter"]
print(f"{n} payloads, {fails} mismatches")
sys.exit(fails != 0)
