# Sensors and flex boards: design study (branch `sensors-flex`)

> **Update, 19 Nov 2026:** the chosen direction is a **3 V, Hubble, battery tag with an MCU**: path D in spirit, on
> a TI CC2340R5. It is specified in [`../hubble/README.md`](../hubble/README.md). This study stays as the background
> for that choice.

**Status:** design study, 19 Nov 2026. Nothing here has been built. Numbers come from datasheets and from
[`sensors/tools/budget.py`](../sensors/tools/budget.py), which reproduces the v8.3 READMEs' own mass figures before
adding anything (0.111–0.122 g for Irulu, 0.187–0.216 g for Hagalu). Weigh and measure the first boards.

**Goal:** add an accelerometer, a light sensor and a pressure sensor to the gantu tags, and find out whether flexible
(polyimide) boards make a better tag: lighter, more repeatable, easier to finish by hand. BLETrack
(SheffieldMLtracking) is used as a second reference design.

---

## 1. The three findings that shape everything else

1. **The IN100 can read sensors without firmware.** Its Config Tool reads up to three I2C devices and puts the raw bytes
   in an advert. It also has an 11-bit ADC (4 channels on GPIOs, plus VCC and chip temperature), a pulse counter and two
   load switches that can power a sensor only while it is being read. So a sensor tag can still be "IN100 + a few
   parts", with no MCU. **What it can't do is compute.** There's no on-tag averaging, activity scoring or heading: the
   tag sends raw register values and the maths happens on the receiving side.

2. **Voltage is the real constraint, not current.** The IN100 runs from 1.1 to 3.6 V, which is why Irulu works on a
   1.55 V silver-oxide cell. Most sensors don't:

   | Part | Function | V_DD min | Current | Runs on a 337? |
   |---|---|---|---|---|
   | **ADXL367** (ADI) | accelerometer | **1.1 V** | 0.18 µA wake-up mode; 0.89 µA at 100 Hz | **Yes** |
   | BMA400 (Bosch) | accelerometer | 1.72 V | 0.85 µA low-power 25 Hz | No |
   | LIS2DU12 (ST, used by BLETrack) | accelerometer | 1.62 V | | No |
   | **BMP581** (Bosch) | pressure | 1.71 V | 1.3 µA at 1 Hz; 0.55 µA standby | No |
   | LPS22DF / ILPS22QS (ST) | pressure | 1.7 V | 1.7 µA at 1 Hz; 0.9 µA power-down | No |
   | **Photodiode into an ADC pin** | light | none | 0 (photovoltaic mode) | **Yes** |

   **Accelerometer and light fit on today's silver-oxide Irulu. Pressure does not:** every small barometer found needs
   ≥ 1.7 V. A pressure tag needs a 3 V cell, the solar tag, a boost converter, or a chip with its own boost (§3).

3. **Find My can't carry sensor data.** The OpenHaystack advert is filled by the public key, so sensor bytes need a
   **second advertising set** (the IN100 has three) heard by something you control: a phone app, a gateway at a
   roost, a receiver along a flyway. Hubble lets an advert carry payload bytes; check how many before planning on it.
   In this design, Find My keeps doing location every 3 s and a sensor advert goes out every 30–60 s.

---

## 2. Sensor options on the IN100 tags

### 2.1 Light: almost free

- One TEMD7000 (0805, the photodiode Hagalu already uses) wired straight to an IN100 ADC pin, unbiased. Its
  open-circuit voltage rises roughly with log(lux), so you get a few hundred mV of dynamic range from dusk to
  full sun with **no added current**.
- About 4 mg and 4 mm². Check the IN100 ADC input range and impedance in the datasheet. If Voc gets too close to the
  rail, add a load resistor, which makes it a current (linear) measurement instead.
- **On Hagalu**, the IN100's own VCC reading (the capacitor voltage) is already a light-history proxy. A separate
  photodiode on an ADC pin gives a cleaner reading.
- Uses: day/night and emergence/return timing at roosts, time in shade vs sun for insects. Bats roost in the dark, so
  for bats light mostly marks when they leave and come back.

### 2.2 Accelerometer: ADXL367

- It is the only small accelerometer found that runs from 1.1 V, so it works on a 337 or 377 directly. 2.2 × 2.3 ×
  0.87 mm LGA, I2C.
- **Activity without an MCU:** set the ADXL367's activity threshold and route INT1 to the **IN100 pulse counter**. The
  sensor advert then carries an activity-event count since the last advert. Add one raw XYZ sample (static tilt and
  orientation) per sensor advert via I2C.
- 0.18 µA in wake-up mode costs about 7 days of a 337's 58-day paper life. At 100 Hz measurement it costs about 12
  days.
- Things to confirm in the Config Tool before layout:
  - that the pulse count can be placed in an advert as dynamic data;
  - that the I2C init sequence (registers written once at boot) fits the OTP.

### 2.3 Pressure: BMP581 (or LPS22DF)

- About 2 × 2 × 0.75 mm, 1.71 V minimum. Put it behind an IN100 **load switch** and trigger a one-shot conversion per
  sensor advert, so the standby current is gone.
- Relative accuracy is a few Pa (sub-metre altitude steps). Absolute altitude needs a ground reference for weather.
- **Keep the vent hole clear of epoxy.** That makes encapsulation a design item: a dam ring, or Kapton over the vent
  while potting.

### 2.4 Not now

- **Magnetometer / heading** (LSM303AGR in the old D3 plan). It needs ≥ 1.71 V, a hard-iron calibration and
  on-tag maths to be useful. With the IN100 you'd send raw XYZ and compute heading afterwards.
- That only makes sense once there is an MCU (path D below), or for a bat-sized tag.

---

## 3. Power paths for a sensor tag

Output of `budget.py`. Find My every 3 s plus a sensor advert every 30 s. 1.5 µC per sensor read is an
**assumption**: measure it. "Planning life" is half of the paper capacity, as the Irulu README advises for
silver-oxide cells.

| Configuration | Avg current | Cell | Life to empty | Planning life (½) | Highest sensor V_min |
|---|---|---|---|---|---|
| Irulu v8.3 (no sensors) | 6.00 µA | 337 SR (1.55 V) | 58 d | 29 d | 1.10 V |
| Irulu v8.3 (no sensors) | 6.00 µA | 377 SR (1.55 V) | 188 d | 94 d | 1.10 V |
| Irulu-S: + light + ADXL367 wake-up | 6.82 µA | 337 SR (1.55 V) | 51 d | 25 d | 1.10 V |
| Irulu-S: + light + ADXL367 wake-up | 6.82 µA | 377 SR (1.55 V) | 165 d | 82 d | 1.10 V |
| Irulu-S: + light + ADXL367 100 Hz | 7.53 µA | 337 SR (1.55 V) | 46 d | 23 d | 1.10 V |
| Irulu-3V: + light + ADXL367 + BMP581 | 6.91 µA | MS412FE (3 V) | 6 d | 3 d | 1.71 V |
| Irulu-3V: + light + ADXL367 + BMP581 | 6.91 µA | MS414GE (3 V) | 12 d | 6 d | 1.71 V |
| Irulu-3V, sensor advert every 60 s | 6.55 µA | MS414GE (3 V) | 13 d | 6 d | 1.71 V |

| Path | What it is | Sensors | Good for | Main cost |
|---|---|---|---|---|
| **A. Irulu-S** | Today's Irulu + photodiode + ADXL367 | light, activity, tilt, chip temperature | Longest life; lowest risk; same cell and finishing steps | No pressure |
| **B. Irulu-3V** | Irulu on a Seiko **MS414GE** (3 V, 2 mAh, 4.8 × 1.4 mm, 0.08 g: same diameter as a 337 and lighter) | + pressure | Short deployments; lighter than Irulu + 337 | ~12 days paper life; rechargeable cell, so charge it before fitting. Also 100 Ω, so C1 still has to carry the burst; rerun `burst_sim.py` at 3 V |
| **C. Hagalu-S** | Solar tag + sensors | light, pressure, tilt while lit | Diurnal insects | Nothing at night or in roosts. A poor fit for bats and for nocturnal moths such as *Acherontia* |
| **D. DA14531 tag** (BLETrack's chip) | Renesas SoC with an MCU and a built-in **boost from 1.1–1.65 V** that can supply external loads | All three, **with on-tag summaries** (activity counts, pressure min/max, heading) | The science version; sensors on a silver-oxide cell | Real firmware (SDK6, Keil). Boost-mode boot errata with a >50 µA load on VBAT_HIGH, so gate the sensors. WLCSP or FCGQFN24 placement at JLC to check |

Also possible: a nanopower boost converter (or Nordic's nPM2100-class PMIC), switched on by an IN100 load switch only
for the pressure read. It works on paper, but it adds an inductor, a part and a start-up timing problem, so try it only
if A and B both fall short.

**Recommendation:**

1. **Build A first.** It needs one ADXL367, one photodiode, two 0402s and a new outline, and it reuses everything Irulu
   has proven.
2. **Put B on the same panel as a variant.** It is the same copper with a BMP581 footprint populated, and a 3 V cell
   instead of a 337 on the same 4.8 mm pads.
3. **Treat D as the separate, longer project** if on-tag summaries turn out to matter.

---

## 4. Flex boards

### 4.1 Mass: the board is most of the tag

At 0.6 mm FR4 the board is about half of Irulu's mass (without the cell) and about 60 % of Hagalu's. A 2-layer JLC
flex (25 µm polyimide core, coverlays, 18 µm copper, ≈ 0.11 mm) with a 0.15 mm PI stiffener only under the
IN100/C1/crystal comes to roughly a quarter of the FR4 board's mass:

| Tag | Sensors | Board | Board mg | Tag without cell |
|---|---|---|---|---|
| Irulu | none | FR4 0.6 mm (v8.3) | 58–65 | 0.111–0.122 g |
| Irulu | none | FR4 0.4 mm | 42–50 | 0.095–0.107 g |
| Irulu | none | **Flex + PI stiffener** | 16–20 | **0.069–0.077 g** |
| Irulu | light + ADXL367 | FR4 0.6 mm | 70–79 | 0.136–0.153 g |
| Irulu | light + ADXL367 | **Flex** | 18–23 | **0.084–0.097 g** |
| Irulu | light + ADXL367 + BMP581 | FR4 0.6 mm | 79–88 | 0.152–0.171 g |
| Irulu | light + ADXL367 + BMP581 | **Flex** | 20–25 | **0.093–0.108 g** |
| Hagalu | none | FR4 0.6 mm (v8.3) | 112–126 | 0.187–0.216 g |
| Hagalu | none | **Flex** | 30–38 | **0.105–0.128 g** |
| Hagalu | light + ADXL367 + BMP581 | **Flex** | 34–43 | 0.129–0.159 g |

**The headline:** a flex Irulu with all three sensors (≈ 0.10 g) is lighter than today's rigid Irulu with none
(≈ 0.12 g). On a 3 V MS414GE, the whole sensor tag comes to **≈ 0.17–0.19 g against ≈ 0.25 g for v8.3 + 337**.
Flex is what makes adding sensors free in mass.

### 4.2 Beyond mass: where flex could make a *better* tag

| # | Idea | What it fixes | Risk |
|---|---|---|---|
| **F1** | **Drop-in flex:** same outlines and layout, polyimide, ENIG, PI stiffener under U1/C1/Y1 | Mass (above). The tail cuts with scissors, not cutters | Lowest. A QFN on unstiffened flex will crack, hence the stiffener. On Irulu the epoxied cell also stiffens the body |
| **F2** | **Fold-over + tab:** a flex flap from the rim folds round the cell edge and is silver-epoxied to the can | Removes the hand-bent + wire, the most variable finishing step | Bend radius ≥ ~10× thickness (≈ 1 mm), so fine. The flap must not reach the − cap |
| **F3** | **Sensor flap folded under** the body (or laid flat along a bat's back) | Adds sensors without growing the Ø 7.2 mm outline; keeps the BMP581 vent on an outer face | Fold position tolerance; epoxy must lock the fold |
| **F4** | **Antenna on the flex:** a λ/4 (≈ 31 mm) trace on a 0.5–0.8 mm strip, or a printed dipole (BLETrack uses printed antennas) | Every tag gets the same antenna length, and there's no solder joint at the RF pad (a likely field failure point) | ≈ 3–5 mg against ≈ 2 mg of wire. The strip is stiffer than wire on an insect. Needs an RSSI A/B test |
| **F5** | **Conformal Hagalu:** photodiode body curved to a thorax | Lower profile, better adhesion, less drag | Photodiodes are rigid 0805s, so it curves only between parts |

JLC builds flex with SMT assembly, but its panel rules differ from rigid (a local fiducial per unit, rails for
assembly). Flex can't share a panel with the FR4 tags, so it is its own order. JLC does not do true rigid-flex; flex
plus stiffener is the equivalent.

### 4.3 How to judge "better" (bench A/B)

Build the same circuit rigid and flex (F1), plus F2 and F4 on the flex panel. Then measure:

1. **Mass:** each tag weighed bare, finished and potted.
2. **RF:** RSSI at 1 m at 8 orientations, wire antenna vs F4, before and after epoxy.
3. **Network yield:** Find My reports per hour for tags left at a fixed test site.
4. **Assembly:** minutes per tag to finish; how many fail at first power-up.
5. **Mechanical:** 100 bend cycles at the neck and flap; a drop test; epoxy adhesion after a night at 4 °C.

---

## 5. What BLETrack adds

BLETrack's 2026 tags use:

- a **DA14531** WLCSP;
- an **LIS2DU12** accelerometer;
- a Seiko **CPH3225A** reflowable rechargeable chip cell, which JLC can place, so no hand-fitted cell;
- **printed antennas**;
- boards about **0.2 mm thick** (0.11 mm core);
- an FPC plug for programming and charging.

Their tags are also a different kind of system: the bee tag *receives* adverts from rotating beacons, logs them, and is
read out after recapture.

Two ideas worth borrowing:

- a machine-placed rechargeable cell;
- a thin board with a printed antenna.

**Licence:** BLETrack is GPL-3.0, while gantu-tag is CC BY 4.0 (hardware) and MIT (code). Don't copy their files into
this fork. Treat them as a reference and re-derive anything used.

---

## 6. Proposed next steps

1. **Irulu-S / Irulu-3V layout** in `irulu_s/` (copy of `irulu/`, generated by `design.py` as before). Hardware:
   - ADXL367 on I2C (GPIO2/3, as on SparkFun's Qwiic wiring);
   - its INT1 to the pulse counter;
   - the photodiode on an ADC GPIO;
   - a BMP581 footprint behind load switch SW0 (fitted on the 3V variant only).

   Panel variants **S** (337, no BMP581) and **P** (MS414GE, BMP581 fitted).
2. **Config Tool dry run** on a SparkFun NanoBeacon board with ADXL367 and BMP581 breakouts:
   - prove the I2C read sequences, the pulse count and the two advert sets before anything is burned to OTP;
   - measure the charge per sensor read, to replace the 1.5 µC assumption.
3. **Flex F1 of Irulu-S**, with F2 (cell tab) and F4 (printed antenna) as panel variants.
4. **Decoder:** a small Python/`bleak` script (and an R reader for the logs) that turns the sensor advert bytes into
   activity, tilt, lux and pressure.

## Sources

- IN100 datasheet (InPlay): https://www.mouser.com/catalog/specsheets/InPlay_IN100_datasheet.pdf
- IN100 I2C sensor tutorial: https://inplay-tech.com/blog/building-a-wireless-temperaturehumidity-sensor-using-the-inplay-in100
- ADXL367 datasheet (ADI): https://www.analog.com/en/products/adxl367.html
- BMA400: https://www.bosch-sensortec.com/products/motion-sensors/accelerometers/bma400/
- BMP581: https://www.bosch-sensortec.com/products/environmental-sensors/pressure-sensors/bmp581
- LPS22DF datasheet (ST): https://www.st.com/en/mems-and-sensors/lps22df.html
- Seiko MS lithium cells: https://www.sii.co.jp/en/
- DA14531 datasheet and FAQ (Renesas): https://www.renesas.com/en/document/dst/da14531-datasheet ,
  https://lpccs-docs.renesas.com/DA14531_FAQs/Hardware.html
- JLCPCB flex capabilities: https://jlcpcb.com/capabilities/flex-pcb-capabilities ,
  https://jlcpcb.com/blog/design-guidelines-flex-pcb-panels
- BLETrack: https://github.com/SheffieldMLtracking/BLETrack
