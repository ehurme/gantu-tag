"""Mass, battery-life and burst budget for the 3 V Hubble sensor tag (run: python3 hubble/tools/budget_3v.py).

Design estimates. Datasheet figures are cited inline; ASSUMPTION marks numbers with no datasheet behind them yet.
Replace them with PPK2 measurements and scale weighings of the first boards.
"""
import math

# ------------------------------------------------------------------ cells (3 V)
# Seiko catalogue (MS = Li-Mn-Si rechargeable). CR632 / CR816: one Chinese supplier's table (Li/MnO2 primary);
# confirm with a second source and weigh samples before designing around them. CR1025: Renata/Panasonic.
CELLS = [
    # name, mAh, g, internal ohm (fresh, end of life), dia x h mm, note
    ("MS414GE", 2.0, 0.08, (100, 300), "4.8 x 1.4", "rechargeable; same Ø as a 337"),
    ("CR632", 13.0, 0.20, (60, 250), "6.8 x 3.2", "primary; verify supplier data (ASSUMPTION: ohm)"),
    ("MS621FE", 5.5, 0.23, (80, 300), "6.8 x 2.1", "rechargeable"),
    ("CR816", 8.0, 0.25, (40, 200), "8.0 x 1.6", "primary; verify supplier data (ASSUMPTION: ohm)"),
    ("CR1025", 30.0, 0.60, (30, 150), "10 x 2.5", "primary; over 0.5 g total, for bats > 15 g"),
]

# ------------------------------------------------------------------ parts (mg). est = estimate from package volume
PARTS = [
    ("CC2340R52E0RGER, QFN24 4x4 (est)", 25, 35),
    ("48 MHz crystal 1612/2016", 3, 5),
    ("ADXL367, LGA12 2.2x2.3 (est)", 7, 10),
    ("BMP581, LGA10 2x2 metal lid (est)", 5, 7),
    ("Bulk C, 100 uF 0805 (burst table; Irulu C1, C141660)", 22, 24),
    ("Decoupling + RF filter, ~9 x 0402", 5, 8),
    ("Light sensor: 0402 LED (or 0805 photodiode +3 mg)", 1, 4),
    ("Solder", 8, 12),
]
ANTENNA = {"wire": (2, 4), "flex trace": (4, 7)}
EPOXY = (20, 40)   # ASSUMPTION: thin coat; vent kept clear. Weigh it.

# Board: same areal densities as sensors/tools/budget.py (calibrated on the v8.3 READMEs)
BOARD_MG_MM2 = {
    "FR4 0.6 mm": (1.39, 1.56),
    "FR4 0.4 mm": (1.39 - 0.37, 1.56 - 0.37),
    "Flex 2L + PI stiffener": (0.075 * 1.42 + 2 * 0.018 * 0.5 * 8.96, 0.075 * 1.42 + 2 * 0.018 * 0.8 * 8.96),
}
STIFFENER = (0.15 * 1.42 + 0.03) * 30   # 0.15 mm PI under the 30 mm^2 parts island (flex only)
BODY_AREA = 57.0   # mm^2: Ø 8.5 mm disc (6.8 mm cell underneath); ASSUMPTION until placement is done


def mass_rows():
    plo = sum(p[1] for p in PARTS)
    phi = sum(p[2] for p in PARTS)
    rows = []
    for bname, (lo, hi) in BOARD_MG_MM2.items():
        flex = bname.startswith("Flex")
        st = STIFFENER if flex else 0
        ant = ANTENNA["flex trace" if flex else "wire"]
        blo, bhi = BODY_AREA * lo + st, BODY_AREA * hi + st
        tlo = plo + blo + ant[0] + EPOXY[0]
        thi = phi + bhi + ant[1] + EPOXY[1]
        rows.append((bname, blo, bhi, tlo, thi))
    return plo, phi, rows


# ------------------------------------------------------------------ power
I_STANDBY_UA = 0.71          # CC2340R52 standby with RTC + RAM retention (datasheet "< 710 nA")
I_ACCEL_UA = 0.89            # ADXL367 at 100 Hz, 2 V (datasheet); used for 25-100 Hz (conservative)
FIFO_SAMPLES = 512           # ADXL367 FIFO (3 axes -> 170 triplets)
Q_DRAIN_UC = {"8-bit": 5.0, "14-bit": 8.0}  # ASSUMPTION: wake + SPI FIFO read + VeDBA maths per drain
Q_ADV_UC = {"GLDO": 13.0, "DC/DC": 8.5}     # ASSUMPTION from TX 5.1 mA (DC/DC, datasheet) / ~9 mA (GLDO, guess)
Q_ENV_UC = 3.5               # BMP581 one-shot (1.3) + wake/ADC/I2C (ASSUMPTION 2.2), every ENV_PERIOD_S
ENV_PERIOD_S = 300


def avg_ua(odr, adv_s, supply="GLDO", fifo="14-bit"):
    drain_period = (FIFO_SAMPLES / 3) / odr
    return (I_STANDBY_UA + I_ACCEL_UA + Q_DRAIN_UC[fifo] / drain_period
            + Q_ADV_UC[supply] / adv_s + Q_ENV_UC / ENV_PERIOD_S)


SCENARIOS = [
    # label, odr, adv interval s, supply, fifo
    ("Bat default: 50 Hz, advert 5 s", 50, 5, "GLDO", "14-bit"),
    ("Moth wingbeat: 100 Hz, advert 5 s", 100, 5, "GLDO", "14-bit"),
    ("Long life: 25 Hz, advert 10 s", 25, 10, "GLDO", "8-bit"),
    ("Bat default with DC/DC inductor", 50, 5, "DC/DC", "14-bit"),
    ("Dense phones (2 s adverts), 50 Hz", 50, 2, "GLDO", "14-bit"),
]


# ------------------------------------------------------------------ burst
def burst_vmin(voc, r, c_eff, i_tx_ma=9.0):
    """One 3-channel advert drawn from cell (voc behind r) + bulk cap. Profile as irulu/tools/burst_sim.py."""
    seg = [(0.5e-3, 1.5e-3)] + [(0.4e-3, i_tx_ma * 1e-3), (0.15e-3, 3e-3)] * 3
    v, lo, dt = voc, voc, 1e-6
    for dur, i in seg:
        for _ in range(int(round(dur / dt))):
            v += ((voc - v) / r - i) / c_eff * dt
            lo = min(lo, v)
    return lo


# Effective capacitance at ~2.5-3 V after DC bias, tolerance and ageing (ASSUMPTION: ~45 % of nominal for small X5R)
CAPS = [("10 uF 0402", 4.5e-6, 1), ("22 uF 0603", 10e-6, 4), ("47 uF 0805", 21e-6, 12), ("100 uF 0805", 45e-6, 23)]
V_FLOOR = 1.9   # CC2340 GLDO min 1.71 V, BMP581 1.71 V: keep 0.2 V margin


def main():
    plo, phi, rows = mass_rows()
    print("## Parts (mg)\n")
    print("| Part | mg |\n|---|---|")
    for n, lo, hi in PARTS:
        print(f"| {n} | {lo}–{hi} |")
    print(f"| **Parts total** | **{plo}–{phi}** |")
    print(f"\nBody {BODY_AREA:g} mm² (Ø 8.5 mm). Antenna: wire on rigid, printed trace on flex. Epoxy {EPOXY[0]}–{EPOXY[1]} mg.\n")

    print("## Finished tag mass (g)\n")
    hdr = "| Board | Board mg | Tag, no cell | " + " | ".join(f"+ {c[0]} ({c[2]:.2f} g)" for c in CELLS) + " |"
    print(hdr)
    print("|" + "---|" * (3 + len(CELLS)))
    for bname, blo, bhi, tlo, thi in rows:
        cells = []
        for c in CELLS:
            lo, hi = tlo / 1000 + c[2], thi / 1000 + c[2]
            mark = " ✓" if hi <= 0.5 else (" ~" if lo <= 0.5 else " ✗")
            cells.append(f"{lo:.2f}–{hi:.2f}{mark}")
        print(f"| {bname} | {blo:.0f}–{bhi:.0f} | {tlo / 1000:.3f}–{thi / 1000:.3f} | " + " | ".join(cells) + " |")
    print("\n✓ under 0.5 g at the high estimate, ~ straddles 0.5 g, ✗ over.\n")

    print("## Average current and life\n")
    print("| Scenario | Avg | " + " | ".join(f"{c[0]} ({c[1]:g} mAh)" for c in CELLS) + " |")
    print("|" + "---|" * (2 + len(CELLS)))
    for lab, odr, adv, sup, fifo in SCENARIOS:
        i = avg_ua(odr, adv, sup, fifo)
        lives = [f"{c[1] * 1000 / i / 24:.0f} d" for c in CELLS]
        print(f"| {lab} | {i:.1f} µA | " + " | ".join(lives) + " |")
    print("\nLife to the cell's rated capacity at 20 °C; plan on ~70 % in the field (cold, pulse losses).\n")

    print(f"## Burst: minimum VCC during one advert (floor {V_FLOOR} V)\n")
    print("| Cell state | " + " | ".join(f"{n} ({m} mg)" for n, _, m in CAPS) + " |")
    print("|" + "---|" * (1 + len(CAPS)))
    for lab, voc, r in [("fresh 3.0 V, 100 Ω", 3.0, 100), ("half 2.8 V, 150 Ω", 2.8, 150),
                        ("late 2.5 V, 250 Ω", 2.5, 250), ("cold end 2.3 V, 400 Ω", 2.3, 400)]:
        vals = []
        for _, c, _ in CAPS:
            v = burst_vmin(voc, r, c)
            vals.append(f"{v:.2f}{'' if v >= V_FLOOR else ' ✗'}")
        print(f"| {lab} | " + " | ".join(vals) + " |")


if __name__ == "__main__":
    main()
