"""Decode (and encode, for tests) the 13-byte gantu Hubble payload, format v1. MIT licence.

Usage:
    python3 hubble/tools/gantu_payload.py 2fe00000f9191b58dac036a800        # one payload
    python3 hubble/tools/gantu_payload.py --csv in.csv --col hex > out.csv  # a column of hex payloads

Format: hubble/docs/payload_v1.md. The R twin is hubble/R/decode_gantu_payload.R.
"""
import argparse
import csv
import sys

# (name, bits) in transmission order, MSB first. Total 104 bits = 13 bytes.
FIELDS = [
    ("version", 3),
    ("alive", 1),
    ("inactive_h", 7),
    ("vedba_cum", 24),
    ("temp", 8),
    ("temp_min24", 8),
    ("pressure", 13),
    ("pressure_min24", 13),
    ("pressure_min24_age_h", 5),
    ("light", 6),
    ("battery", 5),
    ("counter", 8),
    ("reserved", 3),
]
assert sum(b for _, b in FIELDS) == 104

VEDBA_UNIT_G_S = 0.1          # one count = 0.1 g*s
G = 9.80665


def unpack(payload):
    """Raw integer codes from 13 bytes (bytes, bytearray or hex string)."""
    if isinstance(payload, str):
        payload = bytes.fromhex(payload.strip())
    if len(payload) != 13:
        raise ValueError(f"expected 13 bytes, got {len(payload)}")
    v = int.from_bytes(payload, "big")
    out, shift = {}, 104
    for name, bits in FIELDS:
        shift -= bits
        out[name] = (v >> shift) & ((1 << bits) - 1)
    return out


def pack(codes):
    """Inverse of unpack (raw codes -> 13 bytes)."""
    v = 0
    for name, bits in FIELDS:
        c = int(codes.get(name, 0))
        if not 0 <= c < (1 << bits):
            raise ValueError(f"{name}={c} does not fit in {bits} bits")
        v = (v << bits) | c
    return v.to_bytes(13, "big")


def _temp(c):
    return None if c == 255 else c * 0.25 - 20.0


def _press(c):
    return None if c == 8191 else round(300.0 + c * 0.1, 1)


def decode(payload):
    """Physical values. None marks 'no data'. VeDBA is cumulative and wraps at 2^24 counts (difference successive
    messages with vedba_diff())."""
    c = unpack(payload)
    if c["version"] != 1:
        raise ValueError(f"unknown payload version {c['version']}")
    return {
        "version": c["version"],
        "alive": bool(c["alive"]),
        "inactive_h": None if c["inactive_h"] == 127 else c["inactive_h"],   # 127 = >=127 h or never active
        "vedba_cum_counts": c["vedba_cum"],
        "vedba_cum_g_s": round(c["vedba_cum"] * VEDBA_UNIT_G_S, 1),
        "temp_c": _temp(c["temp"]),
        "temp_min24_c": _temp(c["temp_min24"]),
        "pressure_hpa": _press(c["pressure"]),
        "pressure_min24_hpa": _press(c["pressure_min24"]),
        "pressure_min24_age_h": None if c["pressure_min24_age_h"] == 31 else c["pressure_min24_age_h"],
        "light_code": c["light"],                                            # top 6 bits of the 12-bit ADC
        "battery_v": None if c["battery"] == 0 else round(2.0 + c["battery"] * 0.05, 2),  # 0 = not measured / <= 2.0 V
        "counter": c["counter"],
    }


def vedba_diff(earlier_counts, later_counts):
    """VeDBA (g*s) accumulated between two messages, handling the 24-bit wrap. Assumes < 1 wrap between them
    (~1.68e6 g*s: weeks of continuous flight)."""
    return round(((later_counts - earlier_counts) % (1 << 24)) * VEDBA_UNIT_G_S, 1)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("hex", nargs="*", help="payload(s) as 26 hex characters")
    ap.add_argument("--csv", help="CSV file with a column of hex payloads")
    ap.add_argument("--col", default="hex", help="name of the hex column (default: hex)")
    a = ap.parse_args(argv)
    rows = []
    if a.csv:
        with open(a.csv, newline="") as f:
            for r in csv.DictReader(f):
                rows.append({**r, **decode(r[a.col])})
    for h in a.hex:
        rows.append({"hex": h, **decode(h)})
    if not rows:
        ap.print_help()
        return 1
    w = csv.DictWriter(sys.stdout, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
