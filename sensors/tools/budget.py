"""Power and mass budget for gantu-tag sensor and flex variants (run: python3 sensors/tools/budget.py).

Every number here is a design estimate. Sources are given next to each constant; anything marked ASSUMPTION
has no datasheet behind it yet and should be replaced by a bench measurement (PPK2) on the first tags.

Prints two markdown tables:
  1. average current and cell life for each sensor configuration;
  2. finished-tag mass for each board build (0.6 mm FR4 as ordered, 0.4 mm FR4, 2-layer polyimide flex).
"""

# ------------------------------------------------------------------ IN100 (docs/v8_handover.md, irulu/README.md)
Q_ADV_UC = 16.2          # charge per 3-channel advertising event at 0 dBm, uC (handover; ~1.4x at +4 dBm)
I_SLEEP_UA = 0.6         # IN100 sleep current, uA (handover)
FINDMY_INTERVAL_S = 3.0  # Find My / OpenHaystack advert interval used on the v8.3 tags
Q_READ_UC = 1.5          # ASSUMPTION: IN100 wake + one I2C/ADC read sequence, uC. Measure it.

# ------------------------------------------------------------------ sensors (datasheet typicals)
# ADXL367 (ADI): 1.1-3.6 V; 0.18 uA motion-activated wake-up; 0.89 uA at 100 Hz ODR (2.0 V)
# BMA400 (Bosch): 1.72-3.6 V; 0.85 uA low-power mode (25 Hz); 0.16 uA sleep
# BMP581 (Bosch): 1.71-3.6 V; 1.3 uA at 1 Hz low-power (used here as 1.3 uC per one-shot); 0.55 uA deep standby
# LPS22DF (ST): 1.7-3.6 V; 1.7 uA at 1 Hz; 0.9 uA power-down -> must sit behind an IN100 load switch
# TEMD7000 photodiode in photovoltaic mode straight into an IN100 ADC pin: no bias current
SENSORS = {
    "adxl367_wake": dict(i_ua=0.18, vmin=1.1, note="ADXL367 wake-up mode, INT -> IN100 pulse counter"),
    "adxl367_100hz": dict(i_ua=0.89, vmin=1.1, note="ADXL367 measuring at 100 Hz"),
    "bma400_lp": dict(i_ua=0.85, vmin=1.72, note="BMA400 low-power 25 Hz"),
    "bmp581_gated": dict(q_uc=1.3, vmin=1.71, note="BMP581 one-shot, powered by an IN100 load switch"),
    "light_pd": dict(i_ua=0.0, vmin=0.0, note="photodiode Voc on an ADC pin"),
}

# ------------------------------------------------------------------ cells
# 337 from irulu/README.md (Energizer). MS414GE / MS412FE: Seiko catalogue (3 V Li-Mn-Si, rechargeable, 100 ohm).
CELLS = {
    "337 SR (1.55 V)": dict(mah=8.3, g=0.13, v=1.55),
    "377 SR (1.55 V)": dict(mah=27.0, g=0.42, v=1.55),
    "MS412FE (3 V)": dict(mah=1.0, g=0.07, v=3.0),
    "MS414GE (3 V)": dict(mah=2.0, g=0.08, v=3.0),
}

# ------------------------------------------------------------------ configurations
# (name, sensors kept on, sensors read per sensor advert, sensor-advert interval s, cells to report)
CONFIGS = [
    ("Irulu v8.3 (no sensors)", [], [], None, ["337 SR (1.55 V)", "377 SR (1.55 V)"]),
    ("Irulu-S: + light + ADXL367 wake-up", ["adxl367_wake"], ["light_pd", "adxl367_wake"], 30,
     ["337 SR (1.55 V)", "377 SR (1.55 V)"]),
    ("Irulu-S: + light + ADXL367 100 Hz", ["adxl367_100hz"], ["light_pd", "adxl367_100hz"], 30,
     ["337 SR (1.55 V)", "377 SR (1.55 V)"]),
    ("Irulu-3V: + light + ADXL367 + BMP581", ["adxl367_wake"], ["light_pd", "adxl367_wake", "bmp581_gated"], 30,
     ["MS412FE (3 V)", "MS414GE (3 V)"]),
    ("Irulu-3V, sensor advert every 60 s", ["adxl367_wake"], ["light_pd", "adxl367_wake", "bmp581_gated"], 60,
     ["MS412FE (3 V)", "MS414GE (3 V)"]),
]


def avg_current_ua(always_on, reads, sensor_interval):
    i = I_SLEEP_UA + Q_ADV_UC / FINDMY_INTERVAL_S
    i += sum(SENSORS[s].get("i_ua", 0.0) for s in always_on)
    if sensor_interval:
        q = Q_ADV_UC + Q_READ_UC * len(reads) + sum(SENSORS[s].get("q_uc", 0.0) for s in reads)
        i += q / sensor_interval
    return i


def power_table():
    rows = ["| Configuration | Avg current | Cell | Life to empty | Planning life (½) | Lowest sensor V_min |",
            "|---|---|---|---|---|---|"]
    for name, on, reads, interval, cells in CONFIGS:
        i = avg_current_ua(on, reads, interval)
        vmin = max([SENSORS[s]["vmin"] for s in set(on) | set(reads)] or [1.1])
        for c in cells:
            cell = CELLS[c]
            days = cell["mah"] * 1000 / i / 24
            ok = "" if cell["v"] >= vmin + 0.1 else " ⚠"
            rows.append(f"| {name} | {i:.2f} µA | {c} | {days:.0f} d | {days / 2:.0f} d | {vmin:.2f} V{ok} |")
    return "\n".join(rows)


# ------------------------------------------------------------------ mass
# Areal density of the bare board, mg/mm^2 (low, high).
# 0.6 mm FR4: from the v8.3 READMEs (Irulu 58-65 mg / 41.6 mm^2, Hagalu 110-125 mg / 80.8 mm^2).
# 0.4 mm FR4: same copper and mask, 0.2 mm less FR4 at 1.85 g/cm^3.
# Flex: 25 um PI core + two coverlays (~50 um PI+adhesive) at 1.42 g/cm^3, plus 2 x 18 um Cu at 50-80 % fill.
FR4 = 1.85
BOARD = {
    "FR4 0.6 mm (v8.3)": (1.39, 1.56),
    "FR4 0.4 mm": (1.39 - 0.2 * FR4, 1.56 - 0.2 * FR4),
    "Flex 2L ~0.11 mm + PI stiffener": (0.075 * 1.42 + 2 * 0.018 * 0.5 * 8.96, 0.075 * 1.42 + 2 * 0.018 * 0.8 * 8.96),
}
STIFFENER_MG_MM2 = 0.15 * 1.42 + 0.03      # 0.15 mm PI stiffener + adhesive, under the IN100/C1 area only

# Parts: v8.3 READMEs; extra sensor parts are ESTIMATES from package volume (weigh them).
BASE = {
    "Irulu": dict(area=41.6, parts=(53, 57), stiff_area=20),
    "Hagalu": dict(area=80.8, parts=(75, 90), stiff_area=35),
}
ADDONS = {
    "none": dict(area=0, parts=(0, 0)),
    "light + ADXL367": dict(area=9, parts=(13, 17)),            # ADXL367 ~9 mg, PD ~4 mg, 2x 0402, solder
    "light + ADXL367 + BMP581": dict(area=15, parts=(20, 26)),  # + BMP581 ~6 mg, 0402
}


def mass_table():
    rows = ["| Tag | Sensors | Board | Board mg | Tag without cell |", "|---|---|---|---|---|"]
    for tag, b in BASE.items():
        for add_name, add in ADDONS.items():
            if tag == "Hagalu" and add_name == "light + ADXL367":
                continue
            area = b["area"] + add["area"]
            for bname, (lo, hi) in BOARD.items():
                stiff = STIFFENER_MG_MM2 * b["stiff_area"] if bname.startswith("Flex") else 0.0
                blo, bhi = area * lo + stiff, area * hi + stiff
                tlo = blo + b["parts"][0] + add["parts"][0]
                thi = bhi + b["parts"][1] + add["parts"][1]
                rows.append(f"| {tag} | {add_name} | {bname} | {blo:.0f}–{bhi:.0f} | {tlo / 1000:.3f}–{thi / 1000:.3f} g |")
    return "\n".join(rows)


if __name__ == "__main__":
    print("## Power\n")
    print(f"Find My advert every {FINDMY_INTERVAL_S:g} s; sensor adverts on a second advertising set.")
    print(f"ASSUMPTION: {Q_READ_UC} µC per sensor read. ⚠ = cell voltage too close to or below a sensor's minimum.\n")
    print(power_table())
    print("\n## Mass\n")
    print(mass_table())
