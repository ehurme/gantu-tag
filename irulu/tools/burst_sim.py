"""Supply droop during one IN100 advertising event on a 337 silver-oxide cell (run: python3 tools/burst_sim.py).
Cell = Voc behind R_int; bulk cap (effective value after DC-bias derating) across the IN100.
Event model (IN100 datasheet gives only TX currents): 0.8 ms crystal start at 1.5 mA, then
3 channels x (0.5 ms at TX current incl. PLL ramp + 0.15 ms gap at 3 mA)."""
import numpy as np

def profile(i_tx):
    seg = [(0.8e-3, 1.5e-3)]
    for _ in range(3):
        seg += [(0.5e-3, i_tx), (0.15e-3, 3e-3)]
    return seg

def vmin(voc, r, c, i_tx, dt=1e-6):
    v, lo, q = voc, voc, 0.0
    for dur, i in profile(i_tx):
        for _ in range(int(round(dur / dt))):
            v += ((voc - v) / r - i) / c * dt
            lo = min(lo, v)
            q += i * dt
    return lo, q

# effective capacitance at ~1.5 V after X5R DC-bias derating
# (assumes roughly 20 % DC-bias loss for 6.3 V X5R parts)
# v7 variants: A/C/D = 47 uF 0603 + 100 nF; B/E = 47 uF 0603 + 22 uF 0402 (22 uF 0402 taken as ~15 uF at 1.5 V)
caps = [("10 uF 0402 (v4)", 8e-6), ("47 uF (v7 A, C, D)", 38e-6), ("47 + 22 uF (v7 B, E)", 53e-6),
        ("100 uF 0805 (v5)", 80e-6)]
cells = [("fresh, 20 C (80 ohm)", 1.55, 80), ("cold / half used (150 ohm)", 1.53, 150),
         ("near end of life (250 ohm)", 1.50, 250)]
for i_tx, name in ((9.1e-3, "0 dBm, 9.1 mA"), (13.8e-3, "+5 dBm, 13.8 mA")):
    print(f"\nTX {name}: minimum supply voltage during one advertising event (IN100 needs >= 1.1 V)")
    print(f"{'bulk cap (effective)':24s}" + "".join(f"{c[0]:>30s}" for c in cells))
    for cname, c in caps:
        row = ""
        for _, voc, r in cells:
            lo, q = vmin(voc, r, c, i_tx)
            row += f"{lo:>26.2f} V {'ok' if lo >= 1.2 else ('!!' if lo < 1.1 else ' ~')}"
        print(f"{cname:24s}{row}")
lo, q = vmin(1.55, 80, 80e-6, 9.1e-3)
print(f"\ncharge per event at 0 dBm: {q*1e6:.1f} uC")
for T in (1, 2, 3, 5, 10, 60, 600):
    i_avg = 0.625e-6 + q / T
    print(f"interval {T:>4d} s: average {i_avg*1e6:6.2f} uA -> {8.3e-3/i_avg/24:5.0f} days on 8.3 mAh,"
          f" {4.15e-3/i_avg/24:4.0f} days on the first half (ignoring self-discharge)")
# Storage: the OFF jumper holds CHIP_EN at GND; the pull-up then carries VCC / R1 (+ 10 nA in the IN100).
print()
for r1, var in ((1e6, "A, B"), (100e3, "C, E"), (10e6, "D")):
    i_store = 1.55 / r1 + 10e-9
    print(f"storage with OFF bridged, R1 = {r1/1e6:g} Mohm (variants {var}): {i_store*1e6:.2f} uA -> "
          f"{i_store*24*30*1e3:.2f} mAh per 30 days ({i_store*24*30/8.3e-3*100:.0f} % of a 337)")
