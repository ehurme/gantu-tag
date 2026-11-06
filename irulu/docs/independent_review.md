# Independent review: IN100 insect tags v8 (D1 battery, D2 solar v8.2), 3 Nov 2026

The review is based on datasheets and first-principles arithmetic. No project files were edited. My scripts are in
`docs/review_scripts/` (copied from the reviewer's working folder):

- `d1_burst.py` and `d1_powerup.py`: D1 checks
- `d2_static.py`: D2 open-circuit voltage, light thresholds and dark current
- `d2_dyn.py` and `d2_dyn2.py`: D2 dynamics, re-implemented from `solar_sim.py` for 6 PDs with no blocking diode
- `lux_to_iph.py`: daylight to photocurrent, using the ASTM G173 spectra
- `murata_c.py`: the Murata SPICE model evaluated

**Source access.** curl could not reach LCSC, TI, Mouser, onsemi or TXC (proxy 403). I read them through WebFetch,
which returns text only, so figures could not be read.

**IN100 datasheet versions.** The LCSC 2024 PDF could not be retrieved. I used two others:

- **V2.4, 25 Jun 2026**, Mouser-hosted, via WebFetch. Table numbers below refer to it.
- **V1.3, 2022**, SparkFun's GitHub copy. I rasterised it for the pin figure, the reference schematic, Fig. 18 and the
  QFN POD.

Anything marked *est.* is my own estimate and is less certain.

---

## 1. Findings, most serious first

No BLOCKER turned up in the copper, the pinouts or the polarities. I checked:

- the IN100 QFN18 pads and EP against the POD
- the X2SON pin map against TI
- the 1612 crystal diagonal pads
- the PD anodes towards VCC
- D2's cathode on CHIP_EN

The serious items are value and configuration choices that can still be changed in the BOM, CPL or OTP before
ordering.

### F1. SHOULD-FIX (high): the bulk capacitance is overestimated in every simulation

The designer assumed 100 µF at 1.5 V ≈ 80 µF.

**Evidence**

- Murata's own SPICE model of GRM21BR60J107ME15 (0 V DC, 25 °C, small signal) gives **72 µF at 120 Hz–10 kHz**
  (`murata_c.py`) before any DC bias. The 100 µF rating is at 0.5 Vrms.
- On top of that, at 1.5 V:
  - X5R 0805 6.3 V DC bias: typically −15 to −30 % (Murata DC-bias data not retrievable, est.)
  - tolerance: −20 %
  - X5R at −10 °C: about −5 %
  - class-II aging: −3 to −6 %
- **Realistic C_eff is 55–65 µF typical and ≈ 45 µF worst case.** C3 10 µF adds only ≈ 5–8 µF.

**Consequences**

- Every burst margin in `burst_sim.txt` and `solar_sim.txt` is optimistic by 0.05–0.15 V.
- F2, F3 and F4 below follow from this.

**Fix**

- Re-run all margins with 55 µF (typ) and 45 µF (worst).
- Measure a fitted C1 at 1.5 V on the first boards: discharge it 1.6 → 1.4 V with a known current and time it.

### F2. SHOULD-FIX (high): D1 V1's 1 k / 100 nF enable races the slow cell charge-up on a 337

**Evidence**

- V2.4 §5.2 says VCC must reach its final value before, or at the same time as, CHIP_EN. Fig. 18 shows CHIP_EN rising
  after VCC passes 90 %, with t > 0.
- With a 337 (75–85 Ω at 40 Hz, Energizer) and 55–80 µF, VCC charges with τ = 4.4–6.4 ms. At 150–250 Ω (cold or worn)
  τ is 8–20 ms. EN tracks VCC with only 0.1 ms lag.
- So the IN100 boots and runs its first advert while VCC is still rising. `d1_powerup.py` shows the first event
  starting at 0.9–1.35 V and dipping to **0.77–1.21 V** for R = 80–250 Ω. Most of those cases go below 1.1 V, which
  means brown-out lock: the chip needs VCC < 0.1 V for 10 µs to recover.
- On a 364 or 377 (5–15 Ω) the race does not exist.
- SparkFun's 1 k / 100 nF works because their board runs from a 3 V coin cell with 2 V of headroom.

**Fix**

- Make V1's enable slow compared with the cell's τ: **R1 1 MΩ + C2 100 nF** or **100 kΩ + 1 µF** (τ = 100 ms ≫ 20 ms).
  The IN100 then sees the documented OFF state (VCC up, CHIP_EN low) followed by a clean OFF→ON.
- Alternatively, use the OFF-bridge procedure for all tags. Bridging OFF on V1 for the few minutes of cell fitting
  costs 1.55 mA × 10 min ≈ 0.26 mAh, about 3 % of a 337.

### F3. SHOULD-FIX (high): D2 S6 can brown-out-lock in dim light, through an unpublished IN100 threshold

**Evidence**

- The datasheet gives only "≥ 0.6·VCC is high" for CHIP_EN. There is no VIL and no hysteresis; the pin type is
  "Analog".
- The IN100's actual turn-off ratio, K_off, decides whether it is still on when the second advert comes at t = 3 s.
  With R2·C5 = 3.3 s, CHIP_EN at 3 s is ≈ 1.57·e^−0.91 ≈ 0.63 V, or 0.47·VCC.
- With C_eff = 55 µF, 16.2 µC per advert and K_off = 0.2, `d2_dyn.py` gives **STUCK at 0.5–2 klx**: the first event
  takes VCC to 1.33 V and the second to ≈ 1.0 V.
- With K_off 0.3–0.45 it survives, but only because RB751S40 leakage also drains C5.
- With 45 µF and 19 µC the first event already bottoms at **1.18 V**, leaving 0.08 V of margin.

**Fix (pick one or more)**

- **R2 = 3.3 MΩ** (τ = 1.1 s): CHIP_EN is about 0.1 V at 3 s, so there is exactly one advert per start. This removes
  STUCK in every case I ran.
- **Single-channel advertising** (Config Tool: Advertising Channels). This brings the event charge to ≈ 6 µC, removes
  STUCK even with 10 MΩ, and roughly doubles the low-light advert rate (1 klx: 2.9 → 5.2/min).
- Before choosing R2, bench-measure on a SparkFun IN100 board:
  - the first-advert latency after CHIP_EN rises (see F6)
  - the CHIP_EN turn-off ratio, with a slow RC ramp

### F4. SHOULD-FIX: D1 V2 at max power on a 337 risks a permanently dead tag

**Evidence**

- The datasheet maximum is **+4 dBm** (13.8 mA; the change was in revision V1.4), not +5 dBm.
- Lowest VCC per event at +4 dBm (23.3 µC):

  | C_eff | fresh | cold / half used | end of life | cold end of life |
  |---|---|---|---|---|
  | 55 µF | 1.21 V | 1.16 V | 1.11 V | 1.08 V |
  | 45 µF | 1.16 V | 1.09 V | 1.03 V | 0.99 V |

- Once the tail is cut, nothing can pull VCC under 0.1 V, so a lock is permanent.

**Fix**

- Program 0 dBm on 337s. At 55 µF that gives 1.32 / 1.27 / 1.23 / 1.20 V.
- Reserve +4 dBm for 364/377 cells (5–15 Ω), or use +4 dBm on one channel (≈ 8 µC per event).
- Rename the variant "+4 dBm".

### F5. SHOULD-FIX (procurement): IN100-Q1-R-RC1I has been dropped from InPlay's datasheet

**Evidence.** V2.4 revision history, 6/25/2026: "Removed IN100-Q1-R-RC1I, IN100-D1-R-RC1I". The ordering table now
lists only:

- Q1-R-YC1I and Q1-R-YC1F (QFN18 3 × 3 × **0.55 mm**)
- D1-R-YC1I
- W10 WLCSP

**Fix**

- Buy every RC1I you will need now; LCSC had 753 on 2 Nov.
- For the next revision, check the YC1I POD (V2.4 Figure 24) against the footprint. It is also ≈ 4–5 mg lighter (est.).

### F6. SHOULD-FIX (verify before relying on S6): three IN100 behaviours the design depends on are unpublished

1. **Time from CHIP_EN high to the first advert.** If the first advert waits one interval, S6 with 10 MΩ gives
   **0 adverts at 0.5–2 klx** (sim), and R2 = 3.3 MΩ would give none at all.
2. **CHIP_EN input current.** V1.3/V2.4 give only I_VCC = 10 nA with CHIP_EN = 0 V, which bounds a pull-up but not a
   pull-down. V2 and N6 (1 MΩ) and S6 (10 MΩ hold) assume it is ≪ 100 nA.
3. **CHIP_EN turn-off point and hysteresis** (F3).

**Fix.** Spend half a day on a SparkFun board: swap R2 (1 k) for 1 MΩ and 10 MΩ, add 330 nF, and power from
1.55 V through 82 Ω plus 100 µF. With a PPK2 or scope, measure:

- enable-to-first-TX time
- charge per event at 1.5 V
- the CHIP_EN voltage at turn-off on a slow ramp, and any chatter

### F7. NOTE: N6 (R1 1 MΩ / 330 nF, no supervisor) will brown-out-lock

**Evidence**

- CHIP_EN follows VCC (τ 0.33 s), which is the WLCSP case.
- The IN100 starts wherever its unpublished POR releases, with almost no charge above the 1.1 V floor.
- `d2_dyn.py` gives STUCK at every light level below 5 klx for POR guesses of 1.0, 1.3 and 1.5 V. It recovers only when
  a night takes VCC under 0.1 V.

**Fix.** Keep N6 only as a labelled experiment. Don't deploy it.

### F8. NOTE: CHIP_EN absolute maximum is "−0.3 V to **VCC**" (V2.4 Table 15), not VCC + 0.3

**Evidence**

- C5 (S6) holds CHIP_EN at ≈ VCC_start − 0.12 V while VCC sags. After the first event CHIP_EN sits **0.24 V (55 µF)
  to 0.38 V (45 µF) above VCC for about a second**.
- V2's 1 MΩ / 10 nF does the same for milliseconds, by 0.2–0.3 V.

**Assessment.** Almost certainly benign: an ESD diode only conducts above ≈ 0.4–0.5 V. It is still formally outside the
absolute maximum.

**Fix**

- Ask InPlay.
- On V2, C2 = 1 nF (τ 1 ms) tracks the sag.
- Do **not** add a Schottky clamp from CHIP_EN to VCC: its reverse leakage would hold CHIP_EN up through R2.

### F9. NOTE: mass budget omits board copper; parts are overestimated

**Board, 2 × 35 µm Cu, 50–80 % fill both sides, 0.73 mm laminate at 1.9 g/cm³, mask**

| Board | Designer (FR4 only) | My estimate |
|---|---|---|
| D1 Ø7.2 mm, 41.6 mm² | 62 mg | **73–81 mg** |
| D2 v8.2, 6.4 × 12.5 mm, ≈ 80 mm² | 119 mg | **141–156 mg** |

**Parts**

| Part | Mass | Source |
|---|---|---|
| C1 GRM21BR60J107ME15 | **23.0 mg** | Murata |
| 1612 crystal | **2.9 mg** | TXC 8Q sheet |
| IN100 QFN18 0.75 mm | ≈ 19 mg | est. |
| 0402 MLCC | ≈ 1.4 mg | est. |
| 0402 resistor | ≈ 0.65 mg | est. |
| TEMD7000X01 | ≈ 3–5 mg | est.; not on Vishay's sheet |
| X2SON | ≈ 1 mg | est. |
| SOD-523 | ≈ 1.5 mg | est. |
| Solder | 5–8 mg | est. |

**Totals**

- D1 parts ≈ 53 mg (designer ≈ 70). D1 without cell ≈ 0.13 g, the same as the designer's figure because the two errors
  cancel.
- D2 v8.2 ≈ 0.22–0.24 g.
- Cells (Energizer): 337 0.13 g; **364/363 0.37 g** (README says 0.32 g); 377/376 0.42 g.

**Fix.** Update the mass tables and weigh the first boards.

### F10. NOTE: bench light will mislead

**Photocurrent per klx at normal incidence** (`lux_to_iph.py`, ASTM G173 spectra, CIE V(λ) fit, two plausible PIN
responses normalised to Ik = 3 µA at 950 nm)

| Light | µA per klx |
|---|---|
| Sun (AM1.5 global or direct) | **1.41–1.47** |
| White LED, 4000 K | **≈ 0.5** |
| Halogen, 2850 K | **≈ 4** |

- An LED lamp needs about 3× the lux of sunlight for the same current. A halogen lamp flatters by about 3×.
- Use sunlight, or calibrate by measuring a single PD's short-circuit current.

### F11. NOTE: programming D2 at 3.3 V forward-biases the photodiode string

- Dark current per PD at 0.55 V: **0.15–7 mA** for n = 2.0–1.0; the log-linear bound through VF = 1 V at 50 mA gives
  60 µA.
- That comes on top of the up-to-50 mA eFuse current. An FT232R's 3V3OUT (50 mA) is not enough; use a ≥ 100 mA, 3.3 V
  ± 10 % supply.
- Power VCC before connecting RX/TX, or put 1–4.7 kΩ in series. Back-powering through GPIO0 (abs max VCC + 0.3) can park
  the IN100 in the UNKNOWN state.
- For D1: never program with a cell fitted (the README already says so).

### F12. NOTE: smaller items

- **Antenna:** fit the AE2 counterpoise wire on every unit. A 31 mm × 0.1 mm Cu wire weighs ≈ 2 mg, and the dipole
  (≈ 73 Ω) matches 50 Ω far better than a λ/4 wire over a 7 mm ground.
- **TPS3831 IDD** is 150 nA typ but **500 nA max**. At 25 °C the start light rises from ≈ 0.33 to ≈ 0.57 klx.
- **VCC ADC:** the datasheet says VCC ≤ 3.0 V if the on-chip VCC or temperature ADC is used. D2 sits at 3.0–3.3 V in
  sun.
- **Series string:** one shaded PD limits the whole string's current. Keep all six equally lit.
- **Leakage:** clean off flux and coat. 10 MΩ nodes and sub-µA budgets are sensitive to humid flux residue.
- **C1 insulation resistance** could not be retrieved. Murata high-CV X5R items are commonly specified at ≥ 50 Ω·F,
  which for 100 µF means ≥ 0.5 MΩ, i.e. up to 3 µA at 1.5 V as a worst-case limit. Typical leakage is tens of nA (est.).
  Measure the self-discharge of a fitted C1, because it matters for D2's 0.16 µA standby.
- **JLC Economic reflow** is a fixed 255 ± 5 °C. The IN100 datasheet recommends a 250 °C peak. MSL3 small packages are
  normally classified to 260 °C, so the risk is low.

---

## 2. Assumptions A–D

### A. IN100 pinout and connections

| Item | Verdict | Evidence |
|---|---|---|
| 1 XO_N, 2 XO_P, 8 GPIO0 = UART RXD, 9 GPIO1 = UART TXD, 13 VDDQ, 16 RF_TX, 17 VCC, 18 CHIP_EN, EP = GND | **Confirmed** | V1.3 Fig. 3 / Table 1, V2.4 Table 1 |
| "3–7 NC" | **Wrong names, OK to leave open** | 3 MGPIO7, 4 MGPIO6, 5 MGPIO5, 6 SW0 (load switch to VCC), 7 SW1 (load switch to GND) |
| "10–12 NC" | **Wrong names, OK to leave open** | 10 GPIO2, 11 GPIO3, 12 MGPIO4 |
| 14/15 RTC crystal | **Confirmed** | 14 RTC_XO_P, 15 RTC_XO_N; optional ("if internal RC used, RTC can remove", V1.3 Fig. 19) |
| Leaving GPIOs open | **Confirmed OK** | Config Tool guide §2.6: GPIOs are high-Z in sleep and input with pull-up (RPU 25 kΩ) when awake; SparkFun leaves them on unpopulated headers |
| VDDQ tied to VCC | **Confirmed OK** | V2.4: "only needed during eFuse programming"; SparkFun ties VDDQ to VCC (Eagle netlist). InPlay's own reference instead brings VDDQ out to an "EFUSE Power" pad |
| No external match on RF_TX | **Confirmed** | V2.4: "does not require external RF matching components when interfacing to a 50 Ω impedance"; Table 14: on-chip matching network |
| No DC block needed | **Confirmed** | SparkFun's E1 "ANTENNA-GROUNDED" trace antenna DC-shorts RF_TX to GND with nothing in series |
| RF_TX ESD | **Note** | ±2 kV HBM (all other pins ±4 kV) |
| EP / footprint | **Confirmed** | POD: lead pitch e = 0.50 and e1 = 0.40 mm (0.40 on the 7-pin sides), lead b = 0.20 mm, EP 1.70 (parallel to the 7-pin rows) × 1.50 mm, matching `QFN_PADS` and the 1.5 × 1.7 EP |

### B. IN100 supply and enable

| Item | Verdict | Value |
|---|---|---|
| VCC operating range | **Confirmed** | 1.1 / 1.5 / 3.6 V (Table 16) |
| VCC absolute maximum | **Confirmed** | −0.3 to 3.9 V |
| CHIP_EN absolute maximum | **Note** | −0.3 to **VCC** (see F8) |
| Brown-out lock | **Confirmed** | "If the VCC is lowered below 1.1 V, it must be lowered below 0.1 V before the IN100 can re-enter the ON state"; OFF means ≤ 0.1 V for ≥ 10 µs; it "can not reliably transition from the UNKNOWN state to the ON state" (V2.3+) |
| CHIP_EN threshold | **Confirmed** | ≥ 0.6·VCC is high |
| CHIP_EN VIL, Schmitt trigger, hysteresis, input current | **Not stated** | Pin type "Analog". The GPIO 0.3/0.7·VCC figures are not stated to apply |
| Power-up order | **Confirmed** | VCC before or with CHIP_EN; VCC may rise with CHIP_EN low (OFF state) |
| Internal POR level | **Not stated** | Only JLC's description mentions "power-on reset" |
| OTP programming | **Confirmed** | VDDQ 3.3 V ± 10 %, up to 50 mA |
| Off current (CHIP_EN = 0 V) | **Confirmed** | 10 nA |
| Sleep current (32 kHz RC, timer) | **Confirmed** | 0.625 µA |
| TX current at 0 dBm | **Confirmed** | 9.1 mA |
| TX current at max power | **Confirmed** | 13.8 mA at **+4 dBm (max)**; all currents at 3.0 V, 25 °C |
| TX current at 1.5 V | **Probably the same** | The RF sub-system runs from an on-chip 1.2 V LDO, so current should be roughly independent of VCC; the ×1.5 case is pessimistic |
| 26 MHz XO start-up | **Confirmed** | 500 µs typ, 1000 µs max |

### C. Charge per advertising event: 16.2 µC is reasonable and slightly conservative

- The designer's profile reproduces exactly: 0.8 × 1.5 + 3 × (0.5 × 9.1 + 0.15 × 3) = 16.2 µC; +4 dBm gives 23.3 µC.
- The datasheet gives no TX duration or gap.
- A 1 Mbps advertisement with 31 bytes of AdvData is 376 µs on air. With PLL/PA ramp, 0.42–0.5 ms per channel is
  consistent.
- At the XO start-up maximum (1.0 ms) with 0.6 ms per channel: 19.7 µC.
- InPlay's PV kit manual (IN1BN-DKA0-AEM100) quotes 3.21 µA at a 5 s interval and 1.88 µA at 10 s. Solving gives
  **≈ 13.3 µC per event + 0.55 µA**.
- InPlay's 2021 slide quotes 1.4 µA at 10 s, i.e. ≈ 9 µC.
- **Planning range: 9–20 µC. 16.2 µC is a good conservative planning value.**

### D. Crystal

| Item | Verdict | Evidence |
|---|---|---|
| 8Q26000008: 26 MHz, CL 7 pF, ESR 80 Ω, ±16 ppm, −30 to +85 °C, 1612 | **Confirmed** | JLC/LCSC pages |
| IN100 crystal requirement | **Confirmed, one correction** | Table 13: ±40 ppm; **ESR 60 typ / 100 max** (60 is not a minimum); CL 6 typ / 8 max pF; C0 0.7 typ / 3 max pF; Lm 17/20 mH; Cm 2.2/3 fF; on-chip CL 0.5–8 pF in 0.5 pF steps |
| CL, ESR, C0 in spec | **Confirmed** | 7 pF and 80 Ω are inside; C0 ≤ 3 pF (TXC 8Q family) is at the limit |
| ±40 ppm total | **Likely, unverifiable** | JLC gives only "±16 ppm stability"; the tolerance at 25 °C (8Q options ±10/20/30 ppm) and aging (±3 ppm/yr) are unknown |
| Lm / Cm | **Unverifiable** | Not published for this part. A 1612 at 26 MHz may have Cm < 2.2 fF, giving slower start-up |
| External load capacitors | **Correct to omit** | Load is on-chip. Set "XO Load Capacitance" in the Config Tool before burning (≈ 6–6.5 pF to allow for strays). Pull is ≈ 15 ppm/pF at C0 = 1 pF and CL = 7 pF (est.), so check the frequency offset on two or three boards |
| Pads 1 & 3 = crystal (diagonal), 2 & 4 = lid/GND | **Probably correct, not verified from the TXC drawing** | Standard TXC 4-pad arrangement; SparkFun's 3225 part maps 1/3 to XO and 2/4 to GND, as InPlay's reference does. Check rotation in the JLC preview: a 90° error puts the crystal on GND |

---

## 3. D1 battery tag

### (i) DC bias of C1

The 80 µF assumption is high; see F1. Murata's model gives 72 µF at 0 V, so the realistic value at 1.5 V is 55–65 µF
typical and 45 µF worst case.

### (ii) Burst dip

The designer's model reproduces to ±0.01 V.

**0 dBm (16.2 µC)**

| C_eff | 80 Ω fresh | 150 Ω cold/half | 250 Ω end of life | 400 Ω cold end of life |
|---|---|---|---|---|
| 88 µF (with C3) | 1.39 | 1.36 | 1.32 | 1.30 |
| 80 µF (C3 removed) | 1.38 | 1.35 | 1.31 | 1.28 |
| 55 µF (realistic) | 1.32 | 1.27 | 1.23 | 1.20 |
| 45 µF (worst) | 1.28 | 1.22 | 1.17 | 1.14 |

**+4 dBm (23.3 µC)**

| C_eff | 80 Ω | 150 Ω | 250 Ω | 400 Ω |
|---|---|---|---|---|
| 88 µF | 1.32 | 1.29 | 1.25 | 1.22 |
| 80 µF | 1.30 | 1.26 | 1.22 | 1.20 |
| 55 µF | 1.21 | 1.16 | 1.11 | 1.08 |
| 45 µF | 1.16 | 1.09 | 1.03 | 0.99 |

- Removing C3 costs 0.01–0.03 V. **Removing it is fine.**
- Keep C4 tight to pins 13/17 with a direct return to the EP vias.
- 364/377 cells (5–15 Ω) at 55 µF: 1.44 V at 15 Ω and 1.36 V at 40 Ω.

### (iii) Silver-oxide cells

| Cell | Impedance at 40 Hz | Capacity to 1.2 V | Test load | Mass | Note |
|---|---|---|---|---|---|
| 337 (Energizer) | **75–85 Ω** | **8.3 mAh** | 100 kΩ | 0.13 g | "continuous low drain"; marked obsolete by Energizer, so source Renata or Maxell SR416SW |
| 364/363 | 5–15 Ω | 23 mAh | 68 kΩ | 0.37 g | "high pulse on demand" |
| 377/376 | 5–15 Ω | 27 mAh | 45 kΩ | 0.42 g | "high pulse on demand" |

- The 80 Ω "fresh" figure is right for a 337 at 21 °C.
- The 150 Ω cold figure is a guess; I added a 400 Ω cold end-of-life column.
- **The cell never sees 9–14 mA.** The capacitor supplies the burst, and the cell supplies ≤ (1.55 − Vmin)/R ≈ 3 mA
  (fresh 337), decaying with τ = R·C = 4–14 ms, every 3 s. That is acceptable for an SR416.
- Without the capacitor, a 337 would sag 0.7 V at 9 mA.

### (iv) Battery life

| Cell | At 16.2 µC/event (6.02 µA) | At 13.3 µC/event (5.06 µA, InPlay data) |
|---|---|---|
| 337 | 57 d (designer's arithmetic confirmed) | 68 d |
| 364/363 (23 mAh, not 19) | **159 d** | 189 d |
| 377 | 187 d | 222 d |

- Self-discharge over these periods is a few percent.
- Silver-oxide voltage stays flat until near empty. "Plan on half" is pessimistic at 0 dBm, but sensible at +4 dBm on a
  337 (F4).

### (v) Enable networks

- **V1, 1 k / 100 nF:** CHIP_EN rises with VCC, not after it.
  - Acceptable only for a fast supply (364/377).
  - On a 337 it races the 4–20 ms charge-up (F2). Change to τ ≈ 100 ms.
  - The OFF bridge on V1 draws 1.55 mA; brief use during cell fitting is fine.
- **V2, 1 MΩ / 10 nF + OFF bridge:** matches the documented sequence exactly (VCC up with CHIP_EN low, then CHIP_EN
  released). This is good.
  - Standby while bridged is 1.55 µA, about 13–14 % of a 337 per month.
  - Requires the CHIP_EN input current to be ≪ 1.5 µA (F6).
  - C2 = 1 nF would avoid CHIP_EN sitting above a sagging VCC (F8).
  - The 9 ms rise at the tail cut is slow but monotonic; the IN100 reference uses 10 k / 100 nF (1 ms).

### (vi) Anything else needed

- Nothing is mandatory.
- Recommended: the AE2 counterpoise wire on every unit.
- Optional: a series 0402 footprint in the RF line for tuning, if space allows (it doesn't on Ø7.2 mm).
- ESD handling on the bare antenna (RF_TX ±2 kV HBM).
- A recovery path for a locked V1 while the tail is on: short + to G briefly. A 337 delivers ≤ 20 mA.

---

## 4. D2 solar tag (v8.2, 6 PDs, no blocking diode)

### Photodiode data (TEMD7000X01, Vishay rev 1.6)

- Vo = 350 mV, Ik = 3 µA at 1 mW/cm² and 950 nm.
- TK(Vo) −2.6 mV/K; TK(Ik) +0.1 %/K.
- Ira at 5 V: **2.4 / 3 / 3.6 µA**, so a ±20 % spread. In a series string the weakest diode sets the current.
- Radiant sensitive area 0.23 mm². Peak 900 nm; λ0.1 range 350–1120 nm.
- VF = 1 V at 50 mA.
- Reverse dark current 1 nA typ, 3 nA max at 10 V.
- Absolute maximum: VR 60 V, Pv 215 mW, Tj 100 °C. **No forward-current rating is listed**; the 50 mA VF test point
  bounds it.
- Ideality n is not given. The single Vo point and TK(Vo) are consistent with n ≈ 1–1.2, so I bracket 1.0–1.5.

### Daylight conversion

- Full-spectrum sun (AM1.5G) is **109.5 lm/W, i.e. 9.1 W/m² (0.91 mW/cm²) per klx**.
- The 0.0079 W/m² per lux (127 lm/W) figure is not a full-spectrum number and should not be used for silicon.
- Result: **1.41–1.47 µA per klx**. The designer's 1.5 µA/klx is **confirmed** for sun at normal incidence.
- Multiply by cos θ for low sun or a tilted thorax.

### Open-circuit voltage of 6 in series

**At 25 °C**

| Light | n = 1.0 | n = 1.2 | n = 1.5 |
|---|---|---|---|
| 0.5 klx | 1.88 V | 1.84 V | 1.77 V |
| 1 klx | 1.99 V | 1.97 V | 1.93 V |
| 5 klx | 2.24 V | 2.26 V | 2.30 V |
| 20 klx | 2.45 V | 2.52 V | 2.62 V |
| 100 klx | 2.70 V | 2.82 V | 3.00 V |

**At 40 °C, n = 1.2:** 1.59 / 1.72 / 2.04 / 2.31 / 2.62 V.

### Light needed to reach VIT+ (≈ 1.687 V) against standby

| Standby load | Temperature | Light needed |
|---|---|---|
| 0.16 µA | 25 °C | **0.25–0.46 klx** (n 1.0–1.5) |
| 0.16 µA | 40 °C | 0.8–1.1 klx |
| 0.5 µA (TPS3831 max) | 25 °C | 0.5–0.7 klx |
| 0.5 µA | 40 °C | 1.0–1.3 klx |

### Advert rate (S6, 3 s interval, 0 dBm, 25 °C, C = 55 µF, 16.2 µC, 10 minutes from empty)

| Light | Adverts per minute |
|---|---|
| 0.3 klx | 0 |
| 0.5 klx | 0.9 |
| 1 klx | 2.9 |
| 2 klx | 7.0 |
| 5 klx | ≈ 19.5 |
| ≥ 10 klx | 20 |

- Continuous adverts at 3 s need ≈ 5.4 µA plus ≈ 0.5 µA of losses, i.e. **≈ 4–4.5 klx** of sun-equivalent light.
- The designer-like case with 88 µF gives 0.6 / 2.5 / 6.4 / 18.7 at 0.5 / 1 / 2 / 5 klx; the lowest VCC is then 1.46 V
  rather than 1.32 V.
- At 40 °C with 200 nA D2 leakage: 0 / 1.5 / 6.1 / 18.9.

### Maximum VCC, IN100 idle, full sun

| Conditions | n = 1.0–1.5 | n = 2.0 |
|---|---|---|
| −10 °C, 100–120 klx | **3.17–3.47 V** | 3.70–3.75 V |
| −20 °C | up to 3.6 V | — |

**Verdict:** under 3.6 V unless n ≳ 1.8, and well under the 3.9 V absolute maximum. Six PDs is right; seven would not
be.

### Removing the blocking diode: OK

- It gains ≈ 0.1–0.15 V, about 2× less light at the start threshold.
- Dark forward current of the string (one PD at V/6), 25 °C:

  | VCC | n = 1.0 | n = 1.5 | 40 °C, n = 1.2 |
  |---|---|---|---|
  | 1.5 V | 0.06 µA | 0.22 µA | — |
  | **1.7 V** | **0.22 µA** | **0.53 µA** | 1.3 µA |
  | 3.3 V | 7 mA | 0.5 mA | — |

- This only discharges the store in the dark, when the tag is off anyway. In light it is already part of the I–V curve.
- At 3.3 V it is safe for the photodiodes (P ≤ 4 mW each) but loads the programmer (F11).

### TPS3831G18DQNR (TI datasheet)

- Pins (DQN): **1 RESET, 2 MR, 3 GND, 4 VDD**, thermal pad to GND or floating. **Confirmed**, and matches the footprint.
- VIT−: **1.628 / 1.67 / 1.695 V**.
- **VHYS: 17 mV typ** (sim used 20 mV).
- td: 120 / 200 / 350 ms.
- IDD: **150 nA typ, 500 nA max**.
- **MR has an internal 20 kΩ pull-up and may be left unconnected** (§8.3.2). **Confirmed.**
- RESET is asserted between V(POR) = 0.6 V and 0.9 V, and **undefined below 0.6 V**. Because D2 can only pull
  CHIP_EN up, a stray high below 0.6 V can charge C5 to < 0.5 V at most, and R2 bleeds it away. This is harmless in
  practice.

### RB751S40 (onsemi)

- IR 300 nA typ, 500 nA max at 30 V (25 °C). Values at 1–2 V are not tabulated.
- Est. 20–80 nA at 25 °C, about ×2 per 10 °C, so ≈ 100–300 nA at 40 °C. That is comparable to R2's 160 nA, so the hold
  τ becomes ≈ 1–3 s and temperature-dependent. It errs in the safe direction (cf. F3).
- VF ≈ 0.1–0.15 V at µA (est.; 0.28 V typ at 1 mA), so CHIP_EN ≈ 0.92·VCC.
- If a well-defined hold time is wanted, use a low-leakage Si diode (VF ≈ 0.45 V at µA still gives 0.73·VCC).

### CHIP_EN input leakage and slow falling edge

- Input leakage is not stated (F6).
- A falling edge that takes seconds into an "Analog" pin with no stated hysteresis could chatter. Each re-enable costs a
  boot plus an immediate advert. R2 = 3.3 MΩ halves the time spent in the threshold band.

---

## 5. JLCPCB Economic PCBA

Checked on jlcpcb.com/capabilities.

| Item | Rule | This design | Verdict |
|---|---|---|---|
| Board thickness | **0.8–1.6 mm** | 0.8 mm | OK (0.6 mm needs Standard) |
| Sides | single side | top only | OK |
| Panel size | 10 × 10 to 250 × 250 mm | 90 × 49 mm | OK |
| Minimum IC pitch | **0.4 mm** | IN100 at 0.4 mm | OK, at the limit |
| Smallest package | **0402** | X2SON 1 × 1 mm, 0.65 mm pitch, is larger | OK |
| JLC part pages | — | TPS3831G18DQNR (C2066667) and IN100-Q1-R-RC1I (C6062024) both "PCBA type: Economic and Standard" | OK |
| Reflow | fixed 255 ± 5 °C | IN100 datasheet recommends 250 °C peak | Low risk (F12) |
| Solder paste inspection | none | 0.4 mm pitch with 0.2 mm mask dams, mask clearance 0 | Acceptable |

**Stock (designer's 2 Nov figures):** TPS3831G18DQNR 52 (re-check on order day); IN100 753 (see F5).

---

## 6. Bench checks to run on a SparkFun IN100 board before burning 40 tags

1. Supply it from 1.55 V through 82 Ω + 100 µF. With a PPK2 or scope, measure:
   - enable-to-first-TX latency
   - charge per event at 0 dBm and +4 dBm, 3 channels and 1 channel
   - the VCC dip
2. Replace the 1 k with 1 MΩ and 10 MΩ:
   - Does it start?
   - What is V(CHIP_EN)? That gives the input current.
   - Ramp CHIP_EN down over about 3 s: record the turn-off ratio and any chatter.
3. Pull VCC down to about 1.0 V while it runs and back up. Does it recover without going under 0.1 V? This shows how
   real the brown-out lock is.
4. Time the discharge of one fitted 100 µF from 1.6 V to 1.4 V at a known current, to get the real C_eff.

## Sources

- InPlay IN100 datasheet V2.4, 2026: https://www.mouser.com/catalog/specsheets/InPlay_IN100_datasheet.pdf
- InPlay IN100 datasheet V1.3 and NanoBeacon Config Tool guide (SparkFun repo):
  https://github.com/sparkfun/SparkFun_NanoBeacon_Board_-_IN100
- InPlay AEM100 PV-kit manual: https://www.mouser.com/datasheet/2/1567/InPlay_06192024_IN1BN_DKA0_AEM100_C1-3478917.pdf
- InPlay RFID Journal slide: https://www.rfidjournal.com/wp-content/uploads/2021/09/Sept27_Award_Theater_1231_InPlay.pdf
- TI TPS3831: https://www.ti.com/lit/ds/symlink/tps3831.pdf
- onsemi RB751S40: https://www.onsemi.com/download/data-sheet/pdf/rb751s40t1-d.pdf
- Vishay TEMD7000X01: https://www.vishay.com/docs/81951/temd7000.pdf
- Energizer 337, 364/363 and 377/376: https://data.energizer.com/pdfs/337.pdf ,
  https://data.energizer.com/pdfs/364-363.pdf , https://data.energizer.com/pdfs/377-376.pdf
- Murata GRM21BR60J107ME15 data (mass): https://static.chipdip.ru/lib/971/DOC031971774.pdf ,
  https://dtsheet.com/model/4734653
- Murata SPICE model (0 V): https://github.com/ArthorH/ModuCard-GPIO-AUX
  (Simulation/Motecarlo-DC/2012_0805/GRM21BR60J107ME15.mod)
- TXC 8Q family: https://www.txccrystal.com/images/pdf/8q.pdf
- TXC 8Q48090003 (mass): https://uploadcdn.oneyac.com/attachments/files/brand_pdf/txc/44/AA/8Q48090003.pdf
- JLCPCB part pages: https://jlcpcb.com/partdetail/TXCCorp-8Q26000008/C5203638 ,
  https://jlcpcb.com/partdetail/C2066667 , https://jlcpcb.com/partdetail/C6062024
- JLCPCB assembly capabilities: https://jlcpcb.com/capabilities/pcb-assembly-capabilities
- ASTM G173 spectra (pvlib 0.16.1 data file)
