# Insect tag v8: handover task list

**For:** the next agent building the v8 order.
**Owner:** Pavan (MPI-AB).
**Written:** 2 Nov 2026. Stock figures were checked at JLCPCB that day; check them again before ordering.

## Goal

Make three separate JLCPCB-ready boards that can go in one cart:

| # | Design | Variants on one panel | Purpose |
|---|---|---|---|
| D1 | IN100 battery tag, about Ø 8 mm | **V1 Reference** and **V2 +5 dBm** | V1 copies a board known to work (SparkFun NanoBeacon), so it is the "should just work" unit. V2 is the field version: cut the tail to start it, and it can transmit at +5 dBm. |
| D2 | IN100 solar tag, about 9 mm | **S5** and **S6** (5 or 6 photodiodes in series) | Runs on broadband photodiodes plus a large capacitor, with no battery. It may work only some of the time, in sun. Ready to use except for the wire antenna. |
| D3 | Sensor check tag on an nRF52840 module | one | Deliberately simple and larger. Measures activity (accelerometer), heading as a mean angle θ with concentration r (tilt-compensated compass), and pressure. Sends the summaries in BLE adverts. |

What the builder does by hand on D1: attach the cell (one big pad on the bottom, plus one short wire to the other side), solder an antenna wire into a plated hole, then epoxy. On D2 the builder only adds the antenna wire.

> **Note on "+5 dBm":** TX power is a setting written to the IN100's one-time-programmable memory (OTP); it is not a hardware option. What the hardware must provide is enough energy for the burst, which here is a 100 µF capacitor.
>
> So V1 and V2 share the same copper and the same bulk capacitor. They differ only in:
> - the CHIP_EN (enable pin) network;
> - how the tag is started;
> - the TX power programmed into OTP.
>
> Either variant can be programmed for +5 dBm. V1 just ships with conservative settings.

---

## 0. Ground rules (read first)

1. **Start from v7. Don't edit v7.**
   - The source of truth is on Pavan's Mac, at `/Users/pavan/Documents/KiCad/insect_tag_v7`, reached through the linked-computer tools.
   - Read `README.md` and everything in `tools/`:
     - `design.py`: parts, nets, outline and tracks, all in code.
     - `gen_footprints.py`
     - `build.py`
     - `variants.py`: mixes BOM variants on one panel.
     - `make_fab.sh`
     - `panel.json`
     - `panel_standard.json`
     - `burst_sim.py`
   - Copy v7 into new folders: `insect_tag_v8_battery`, `insect_tag_v8_solar` and `insect_tag_v8_sensor`.
2. **Do not touch `insect_tag_v3`.** Another session owns it.
3. **No deletes in the Mac folders.** Deletes there aren't permitted. Move unwanted files into a `_to_delete/` subfolder. Never `rm -rf` with globs; it was blocked before, so don't work around that.
4. **Toolchain that worked for v7** (cloud container):
   - **KiCad 7:** the `pcbnew` Python module (`/usr/bin/python3`). If `import pcbnew` fails in a fresh container, install KiCad 7 with apt, or run the pipeline on the Mac.
   - **KiKit 1.6.0** must run under Python 3.12, because `wx` was missing under 3.13:
     - Install: `/usr/bin/python3.12 -m pip install --break-system-packages kikit==1.6.0`
     - Run: `KIKIT="/usr/bin/python3.12 -m kikit.ui" PY=/usr/bin/python3.12 bash tools/make_fab.sh`
   - **DRC:** KiCad 7's `kicad-cli` has no `pcb drc`. Use `pcbnew.WriteDRCReport`.
   - **Final checks in KiCad 10** on the Mac via the Copperpour MCP tools:
     - `open_project`, then `run_drc` and `run_erc`;
     - a 3D render;
     - `get_board_2d_view`.
5. **Lessons from v4 to v7 (don't repeat these mistakes):**
   - **Refill zones after the design rules exist.** `build.py` has `refill()`; keep it. Earlier boards saved a fill that ran to the board edge.
   - Set KiKit `post.refillzones: true`. Otherwise the mouse bites leave the pour cut.
   - Keep KiKit `renameref "{orig}"`, then let `variants.py` write unique designators (`R1_V2_3`, and so on). `{orig}_{n}` emptied the BOM.
   - **Check every copper pour for islands** after each layout change. v7 needed extra GND vias and moved lanes to fix them.
   - Keep tabs and mouse bites away from rim copper.
   - After any loop that tries different board sizes, rebuild at the final size. A test loop once left R = 3.3 mm in the build and produced 162 edge errors.
6. **Packages:**
   - Use **IN100-Q1-R-RC1I** (QFN18, 3 × 3 mm), JLC **C6062024**: 753 in stock, about $2.58 each at qty 1.
   - Don't use DFN8 or WLCSP for this round. Those listings are pre-order or need Standard PCBA with X-ray.
   - Don't use the "RC0I" part; that suffix isn't in the datasheet.
7. **Board and assembly service:**
   - D1 and D2: 2-layer FR4, **0.8 mm**, lead-free HASL, **Economic PCBA, top side only**. Economic accepts only 0.8 to 1.6 mm boards.
   - 0.6 mm needs Standard PCBA and a panel of at least 70 × 70 mm. `panel_standard.json` shows how. Don't use it this round unless Pavan asks.

---

## 1. Parts already checked (JLC, 2 Nov 2026)

| Function | Part | LCSC | Type | Stock | Notes |
|---|---|---|---|---|---|
| BLE SoC | IN100-Q1-R-RC1I | C6062024 | Ext | 753 | QFN18; at least 4 vias in the exposed pad (EP) |
| Crystal 26 MHz | TXC 8Q26000008 (1612) | C5203638 | Ext | 1,313 | 7 pF, 80 Ω, ±16 ppm. Meets datasheet: CL 6 to 8 pF, ESR 60 to 100 Ω, ±40 ppm. No load caps (as SparkFun). |
| Bulk capacitor | 100 µF 6.3 V X5R 0805, Murata GRM21BR60J107ME15L | C141660 | Ext | 27,104 | The large capacitor that covers the TX bursts |
| Mid capacitor | 10 µF 0402 X5R | C15525 | Basic | 10 M | Matches SparkFun's C2 |
| Decoupling | 100 nF 0402 | C1525 | Basic | — | At the VCC pin |
| EN pull-up (V1) | 1 kΩ 0402 | C11702 | Basic | 21 M | SparkFun value |
| EN pull-up (V2) | 1 MΩ 0402 | C26083 | Basic | — | Draws 1.6 µA while the OFF bridge holds EN low |
| EN pull-up (alt) | 100 kΩ 0402 | C25741 | Basic | 8 M | |
| EN capacitor (V1) | 100 nF 0402 | C1525 | Basic | — | SparkFun value |
| EN capacitor (V2) | 10 nF 0402 | C15195 | Basic | — | |
| EN capacitor (alt) | 1 µF 0402 | C52923 | Basic | 10 M | |
| 0 Ω link | 0 Ω 0402 | C17168 | Basic | 11 M | Used to select the solar variant |
| Photodiode | Vishay TEMD7000X01 (0805, 350 to 1120 nm) | C145328 | Ext | 2,559 | $0.87 each. Alternative: VEMD1060X01, C144925. **Avoid PD15-21B**: it is 1206 and passes only IR. |
| Blocking diode | onsemi RB751S40T1G (SOD-523 Schottky) | C232576 | Ext | 46,366 | 0.37 V at 1 mA; ≤ 500 nA leakage at 30 V. Alternative: Nexperia C477990. |
| Supervisor | TI TPS3839G18DBZT (SOT-23) | C2067516 | Ext | 198 | 1.67 V threshold, 150 nA, push-pull active-low output. Fallback only; see D2. |
| BLE module | Seeed XIAO nRF52840 | C17209540 | Ext | 48 | $10.78. Alternative listing: C48405120. |
| Accelerometer + magnetometer | ST LSM303AGR (LGA-12, 2 × 2 mm) | C126671 | Ext | 2,231 | $4.05 |
| Barometer | Bosch BMP581 (LGA-10, 2 × 2 mm) | C5362283 | Ext | 7,242 | $2.42 |
| I2C pull-ups | 4.7 kΩ 0402 | C25900 | Basic | 14 M | |

---

## 2. D1: IN100 battery tag (V1 Reference and V2 +5 dBm)

### 2.1 Circuit (identical copper for both variants)

Start from v7's `design.py` net list and change only what is listed here.

- **Parts kept from v7:**
  - U1: IN100 QFN18.
  - Y1: crystal.
  - Pins VCC and VDDQ: both tied to VCC, as in v7 and SparkFun.
  - At least 4 EP vias.
  - RF pin: goes straight to the antenna hole.
- **Supply capacitors:**
  - C1: 100 µF 0805 (C141660). This is the bulk capacitor.
  - C3: 10 µF 0402 (C15525). New in v8, for parity with SparkFun.
  - C4: 100 nF 0402 (C1525), placed right at the VCC pin.
- **EN network:**
  - R1: from VCC to CHIP_EN.
  - C2: from CHIP_EN to GND.
  - JP1 "OFF": a solder bridge on the tail that ties CHIP_EN to GND. The tail is cut off at the neck to start the tag, as in v7.
- **Cell (+ and −):** see 2.3.
- **J1 programming pads on the tail** (GND, RXD, TXD, +): enlarge them to at least 1.0 × 1.4 mm at a pitch of at least 1.5 mm so they are easy to hand-solder or pogo.
- **Antenna holes:** see 2.4.

### 2.2 Variants (by panel column, through `variants.py`)

| Variant | R1 | C2 | Start-up | Program to | Silk on tail |
|---|---|---|---|---|---|
| **V1 Reference** | 1 k (C11702) | 100 nF (C1525) | Runs as soon as the cell is attached. Never bridge OFF on V1: it would draw 1.5 mA. | 0 dBm, 3 s interval | `V1 NO OFF` |
| **V2 +5 dBm** | 1 M (C26083) | 10 nF (C15195) | Bridge OFF before attaching the cell, then cut the tail to start. | +5 dBm (or 0 dBm), 3 s interval | `V2` |

- Set `PANEL_COLUMNS = ["V1"]*5 + ["V2"]*5` on the v7 2 × 10 KiKit panel. That gives 10 of each.
- `variants.py` currently writes single-letter tail labels. Extend it so labels such as `V1` work.

**Task D1-a.** Read IN100 datasheet Fig. 18 (power-up sequence).
- If it requires CHIP_EN to rise later than VCC by more than SparkFun's RC gives (1 k × 100 nF = 0.1 ms), switch V1 to 100 k + 1 µF (C25741 + C52923, τ = 100 ms).
- Write down the reason in the README.
- If Fig. 18 is silent, keep SparkFun's values. SparkFun ships a working board with them.

**Task D1-b.** Rerun `burst_sim.py` with the v8 capacitors (100 µF + 10 µF + 100 nF).
- Cases: cell ESR of 80, 150 and 250 Ω, at 0 dBm and at +5 dBm.
- Report the minimum VCC in each case.
- v7 results for 100 µF alone, for reference:
  - 0 dBm: 1.38 / 1.35 / 1.31 V.
  - +5 dBm: 1.30 / 1.26 / 1.22 V.
- Find the IN100 minimum VCC in the datasheet and report the margin above it.

### 2.3 Cell attachment ("one big pad on the bottom, one wire")

The cells to support are common silver-oxide watch cells sold on Amazon:
- 337 (Ø 4.8 mm);
- 364/363 and 377/376 (Ø 6.8 mm).

The cell sits on the **bottom** side with its **− cap facing the board**. This orientation is chosen because:
- the wire then goes to the can, and the can is already + potential;
- so a stray wire touching the can's side can't short anything.

Requirements:

1. **Bottom − pad, as large as possible:**
   - Ø 2.0 mm, GND, defined by the solder-mask opening.
   - Look up the − cap diameters of 337, 364 and 377 in the Renata or Energizer datasheets. The pad must stay inside the smallest cap so it can't reach the can's crimped edge.
   - Try centring the cell on the IN100. The GND EP vias then land inside the − pad region, which is at the same potential.
2. **Keep-out under the can edge:**
   - No exposed copper and no vias in the ring where the can's crimped edge sits.
   - That ring runs from r = (cap radius + 0.2 mm) to r = (can radius + 0.3 mm), for every supported cell.
   - Tented vias only if they are unavoidable.
   - Put the extent of each cell outline on B.SilkS as rings, as in v7.
3. **+ pad:**
   - At least 1.5 × 1.2 mm, VCC, on the **bottom** at the disc edge, outside the 337 outline. On 6.8 mm cells the can overlaps it, which is harmless because both are +.
   - Add a mirrored **top** + pad joined to it by 2 vias, so the wire can also run over the edge.
   - Mark both with "+" on silk.
4. **README build steps:**
   1. Put a dab of silver-filled conductive epoxy on the − pad and seat the cell.
   2. Solder a short wire (0.2 mm tinned copper or a 0.1 mm nickel strip) to the + pad.
   3. Bend the wire to the can's side wall and fix it with silver epoxy. **Never solder to the cell.**
   4. Cure, then encapsulate with ordinary epoxy, leaving the antenna free.

### 2.4 Antenna attachment

- **AE1:** plated through-hole, 0.6 mm drill with a Ø 1.1 mm pad. Place it at the disc edge opposite the neck, with the shortest possible trace (under 2 mm) to the RF pin. The IN100 has an on-chip 50 Ω match, and SparkFun uses no external match.
- **AE2:** an identical hole on GND, as an optional counterpoise or second dipole arm.
- **README:** start with a straight wire about 31 mm long (λ/4 at 2.44 GHz in air) and trim while watching RSSI. Use a dipole (AE1 + AE2) when the radiated power matters, for example for Hubble later.

### 2.5 Outline

- Disc of about Ø 8.0 mm: `R_TAG` = 4.0. Keep v7's neck, tail, cut line and silk.
- It may grow to fit the 0805 capacitor and the larger pads. Report the final size and mass. At 0.8 mm FR4, an Ø 8 mm disc is about 74 mg of bare board.

---

## 3. D2: IN100 solar tag (S5 and S6)

**What it does:**
- Photodiodes charge a 100 µF capacitor through a Schottky diode.
- A low-current voltage supervisor holds CHIP_EN low until the capacitor has enough charge, then releases it.
- The IN100 advertises until the capacitor runs down.
- It works in daylight only and keeps no clock overnight. That is fine for Find My. For Hubble, the time counter restarts every morning; flag this in the README.

### 3.1 Circuit

- **IN100 core:** same as D1 (U1, Y1, C1 100 µF, C3 10 µF, C4 100 nF, VCC/VDDQ, EP vias, J1 programming pads on a tail, AE1 and AE2 holes).
- **No battery pads. No R1, C2 or JP1.** CHIP_EN is driven only by the supervisor U2.
- **Harvester:**
  - PD1 to PD6: TEMD7000X01 in series, anode chain toward VCC.
  - Then D1 (RB751S40, C232576), from anode to VCC.
  - D1 stops two things:
    - the capacitor discharging back through the photodiodes in the dark (they would be forward-biased at about 0.5 V each);
    - the programmer's 3 V feeding back into the string.
- **Variant link:**
  - A 0402 footprint, R_SEL, sits across PD6.
  - Variant **S5**: place R_SEL as 0 Ω (C17168); don't place PD6.
  - Variant **S6**: place PD6; don't place R_SEL.
  - Same copper; panel columns `["S5"]*5 + ["S6"]*5`.
- **U2 supervisor.** Requirements:
  - Quiescent current ≤ 0.3 µA.
  - Push-pull output, active-low, wired straight to CHIP_EN.
  - Behaves like a "solar engine" with large hysteresis:
    - releases EN at about 2.0 to 2.4 V;
    - holds EN until VCC falls to about 1.2 to 1.3 V.
  - Why: with only a small hysteresis, the IN100 starts, the first TX burst pulls the capacitor below the threshold, and the tag can get stuck in boot loops. At 0 dBm one advert costs about 16 µC, about 0.16 V on 100 µF.
  - **Fallback:** TPS3839G18 (C2067516, 1.67 V, 150 nA). Its hysteresis is small and fixed. Check whether it gives at least one complete advert per charge cycle.

**Task D2-a.** Choose U2. In order of preference:
1. A JLC-stocked nanopower voltage detector with a separate sense input or built-in large hysteresis.
2. The classic BEAM "solar engine" latch: a voltage detector plus a P-MOSFET and a resistor that keeps the output high until a lower voltage.
3. The TPS3839 fallback.

Justify the choice with numbers and the datasheet hysteresis figure.

**Task D2-b.** Size the string from the TEMD7000X01 datasheet:
- **Open-circuit voltage:** compute Voc per diode against illuminance, from dim indoor light to full sun.
- **Upper limit:** N × Voc(full sun) − V_D1 must stay ≤ 3.6 V (the IN100's absolute maximum).
- **Start threshold:** the string must clear U2's start threshold in shade or overcast light.
- **Current:**
  - Scale the light current from the datasheet value (given at 1 klx).
  - First estimate, to be replaced by the datasheet figure: about 0.23 mm² of sensitive area gives on the order of tens of µA in full sun and a few µA in shade.
  - The IN100 averages about 6 µA at a 3 s interval and 0 dBm (16.2 µC per event + 0.6 µA sleep).
- **Simulation:** extend `burst_sim.py` with:
  - a photocurrent source;
  - D1;
  - U2's thresholds;
  - the IN100's boot and advert charges.
- Report adverts per minute against lux for S5 and S6.
- If 6 in series can exceed 3.6 V in full sun, drop S6 and make the second variant a different U2 threshold instead.

### 3.2 Layout

- **Top side only** (Economic PCBA).
- Photodiodes at the top surface with nothing tall beside them to shade them.
- Round Ø 9 to 10 mm, or about 9 × 10 mm, plus the programming tail.
- 0.8 mm board. Expect about 110 to 130 mg in total; a 0.6 mm or flex version comes later.
- Bottom: GND pour.
- **Storage:** keep the tags in the dark; there is no OFF jumper. The tail is cut after programming only to save mass.

### 3.3 Programming

- The programmer powers VCC at 3.0 V through J1. D1 protects the photodiodes.
- U2 releases EN once VCC is above its threshold.
- Confirm with the IN100 programming guide that the programmer doesn't need to control CHIP_EN. If it does, add a test pad on CHIP_EN through 1 k.

---

## 4. D3: sensor check tag (deliberately simple)

**Purpose:** prove the on-tag summaries work before shrinking anything. Size and mass don't matter much here; a few grams is fine.

### 4.1 Hardware

- **Carrier board:** 2-layer, 0.8 to 1.0 mm, about 21 × 26 mm.
- **XIAO nRF52840** (C17209540; alternative C48405120) on top:
  - Use Seeed's official SMD footprint, including the bottom BAT+ and BAT− pads.
  - Route both of those to large carrier pads (≥ 2 × 3 mm, labelled) for a single-cell LiPo.
  - The XIAO charges the cell over USB-C; keep USB-C reachable.
  - Check with JLC whether they can place the XIAO; if not, it is easy to hand-solder by its castellated edge pads.
- **LSM303AGR (accelerometer + magnetometer):**
  - Follow the datasheet's application diagram exactly, including the dedicated capacitor on its C1 pin and the VDD decoupling.
  - I2C addresses: accelerometer 0x19, magnetometer 0x1E.
  - INT1 (accelerometer) → XIAO D2.
- **BMP581 (barometer):**
  - Decoupling per datasheet; I2C address 0x46 or 0x47 (choose with SDO).
  - INT → D3 (optional).
  - Keep its vent hole clear: no epoxy or conformal coat over it.
- **I2C:** SDA = D4, SCL = D5 (Arduino defaults), with 4.7 k pull-ups (C25900) to 3V3.
- **Magnetometer placement:**
  - Put the LSM303AGR at the far end, at least 5 mm from the XIAO's USB-C shell, its DC-DC inductor and the battery pads.
  - No pour directly under it.
  - Print the X/Y/Z axes on silk.

### 4.2 Firmware

Arduino, Seeed nRF52 non-mbed core with the Bluefruit library. Use the STM32duino LSM303AGR and SparkFun BMP581 libraries, or the vendor APIs.

- **Sensor rates:** accelerometer at 10 to 25 Hz in low-power mode; magnetometer at 10 Hz; barometer at 1 Hz.
- **Activity:**
  - Each second, compute the mean of | |a| − 1 g |, or of a high-passed |a|.
  - The second counts as active if that mean exceeds THR (default 50 mg, settable).
  - Per window W (default 60 s on the bench, 300 s in the field), report:
    - the number of active seconds;
    - the mean dynamic acceleration;
    - an exponential running average (EMA) of the active fraction.
- **Heading (only while active):**
  - Tilt-compensated heading, using low-passed accelerometer data for gravity.
  - Also log the "assume flat" heading, atan2(my, mx), for comparison.
  - Hard-iron calibration: rotate the tag in a figure-8 at boot or on a BLE command; store the offsets in flash.
  - Circular statistics: S = Σ sin θ, C = Σ cos θ.
    - Mean heading θ̄ = atan2(S, C).
    - Concentration r = √(S² + C²) / n, from 0 (scattered) to 1 (steady).
- **Pressure:** mean and median (from a small ring buffer) while active, plus one reading per window when inactive.
- **Advert:** every 1 to 2 s, manufacturer data with company ID 0xFFFF for testing. Suggested 13 bytes:

  | Field | Bytes | Units |
  |---|---|---|
  | version | 1 | |
  | window counter | 1 | |
  | active seconds | 2 | s |
  | mean dynamic acceleration | 1 | mg ÷ 4 |
  | θ̄ | 1 | 0 to 255 maps to 0 to 360° |
  | r | 1 | 0 to 255 |
  | pressure | 3 | Pa |
  | temperature | 1 | °C, signed |
  | battery | 1 | (mV − 2000) ÷ 10 |
  | flags | 1 | |

- **Tools:**
  - USB serial log for bench work.
  - A small Python decoder using `bleak`.
  - nRF Connect on a phone to see the raw bytes.
- **Later (not now):** Hubble SDK or Find My advert sets alternating with the sensor advert.

### 4.3 Bench acceptance

- **Shake test:** shaking raises active seconds; at rest, 0.
- **Heading:** after calibration, rotate in 90° steps on a flat surface. θ̄ should be within ±10° of a phone compass, and r close to 1 while holding steady.
- **Pressure:** carrying the tag up one floor (about 3 m) should change pressure by about 35 Pa.

---

## 5. Fab outputs and ordering

- **For each design:** the build script, the KiCad project (schematic + PCB), and `fab/` containing:
  - the Gerber zip;
  - the BOM with LCSC numbers;
  - the CPL with unique designators;
  - for D1 and D2, the panel files with variants.
- **Panels:**
  - D1: v7 2 × 10 panel → 10 V1 + 10 V2.
  - D2: same panel style → 10 S5 + 10 S6.
  - D3: 5 single boards, or a 2 × 2 panel.
- **One JLC cart, three PCB orders:**
  - 2-layer FR4, lead-free HASL.
  - Thickness: 0.8 mm for D1 and D2; 0.8 or 1.0 mm for D3.
  - Economic PCBA, top side.
  - Ask JLC to confirm part placement.
- **IN100s needed:** 40 (stock is 753).
- **Rotation check:** in JLC's placement preview, check:
  - pin 1 of the IN100;
  - crystal orientation;
  - D1 and photodiode polarity;
  - U2 orientation;
  - LSM303AGR and BMP581 pin 1.

  Fix offsets in the CPL rather than the footprints.

---

## 6. Acceptance checklist (all designs)

- [ ] **DRC with KiCad 7 `pcbnew`:** 0 errors and 0 unconnected on each board and on each panel. Mouse-bite to pour clearance ≥ 0.2 mm.
- [ ] **KiCad 10 (Copperpour MCP on the Mac):** DRC 0; ERC 0 errors (cosmetic warnings listed).
- [ ] No pour islands; every GND region is stitched.
- [ ] 3D renders, top and bottom, saved to `docs/` and checked by eye: cell rings, pads, cut line, antenna holes.
- [ ] `burst_sim` (D1) and the solar simulation (D2) results recorded in the README.
- [ ] **README for each design:**
  - circuit;
  - variant table;
  - hand-assembly steps (cell, antenna, epoxy);
  - programming steps (OTP: Find My or Hubble);
  - bring-up test;
  - mass estimate.
- [ ] Stock rechecked for every LCSC number on order day.
- [ ] Zip each design, and copy all three folders to `/Users/pavan/Documents/KiCad/`. No deletes; use `_to_delete/`.

## 7. Bring-up plan (write it into the READMEs)

1. **D1 on the bench:**
   - Power from a 1.45 V bench supply through a 150 Ω series resistor, standing in for the cell's resistance.
   - Program V1 at 0 dBm and V2 at +5 dBm.
   - Check the adverts in nRF Connect.
   - Measure average current with a current profiler (Nordic PPK2 or µCurrent).
   - Then fit a real 337 and a real 377.
2. **D2:** count adverts per minute under a desk lamp, in shade outdoors and in full sun, with lux logged by a phone.
3. **D3:** run the bench tests in §4.3.

## 8. Defaults the agent should use without asking

- Advert interval: 3 s.
- Firmware for the first test units: Find My (OpenHaystack static key). Hubble is an OTP choice later and needs no hardware change.
- Cells: 337 for the lightest build, 377 for the longest life.
- If a part is out of stock, take the nearest JLC equivalent with the same package and specification, and note it in the README.
