# 3 V Hubble sensor tag (working name *Irulu-H*)

**Status:** design spec, 19 Nov 2026. No board has been laid out yet. Every figure is an estimate from
[`tools/budget_3v.py`](tools/budget_3v.py); weigh and measure the first boards.

**Goal:** a battery tag for small nocturnal animals (bats, large moths), **≤ 0.5 g**. It reports through the
**Hubble** network:

- cumulative VeDBA;
- an alive/dead flag;
- tag temperature;
- pressure, and the 24 h minimum pressure;
- light.

Everything fits Hubble's 13-byte custom payload ([`docs/payload_v1.md`](docs/payload_v1.md)).

## Why this isn't an IN100 tag

The IN100 can send raw sensor bytes, but it can't add up VeDBA, keep a 24 h minimum or decide alive/dead. That needs
a microcontroller. The **TI CC2340R5** is a BLE SoC with a Cortex-M0+, and it is on Hubble's supported list (the TI
CC23xx family, with Hubble's TI toolkit). It is also:

- available in a **4 × 4 mm QFN24**, `CC2340R52E0RGER`;
- stocked at JLC as **C20416850** (~2,200 there, ~6,000–9,000 at LCSC, ≈ $1.40);
- runs from **1.71–3.8 V**, with < 0.71 µA standby with the RTC running.

The nRF54L15 (Hubble's own reference chip) is the alternative. Its small package is a 2.4 × 2.2 mm WLCSP, which
is harder to build at JLC, so it waits for a later revision.

Hubble's clock tolerance is loose: ±24 h, with ≥ 500 ppm oscillator accuracy recommended. So the CC2340's internal
low-frequency oscillator should do, and **no 32 kHz crystal** is needed. A footprint stays on the board, unfitted, as
a fallback.

## Circuit

| Ref | Part | LCSC / JLC | Notes |
|---|---|---|---|
| U1 | CC2340R52E0RGER (QFN24 4×4) | C20416850 | GLDO supply mode (no inductor), so it runs right down to the cell's 2.0 V end. An optional 0402 DC/DC inductor footprint can save ≈ 14 % current while the cell is above 2.2 V |
| Y1 | 48 MHz crystal, 1612 or 2016 | TBD | Per TI's CC2340R5 RGE reference design. Load capacitance is on chip |
| U2 | ADXL367BCCZ-RL7 accelerometer | C17643415 | **JLC "Standard only", stock 0–67 at LCSC**: pre-order or consign. On SPI; INT1 to U1 |
| U3 | BMP581 pressure + temperature | C5362283 | Shares the SPI bus (own CS). **Powered from a U1 GPIO**, so it draws nothing between readings. Keep the vent clear of epoxy |
| D1 | 0402 LED as light sensor (or TEMD7000 photodiode) | TBD | Photovoltaic, no bias, on a U1 ADC pin with ~10 nF to ground so the ADC sample doesn't load it |
| C1 | 100 µF 0805 X5R (as Irulu) | C141660 | Burst reservoir; see the burst table below. 47 µF is enough only with the DC/DC fitted |
| C2–C8 | decoupling, 0402 | basic parts | VDDS, VDDR, DCOUPL and the sensors, per the TI reference design and the sensor datasheets |
| L1, C9, C10 | RF low-pass/match, 0402 | TBD | TI reference values, to the antenna feed |
| J1 | SWD pads on the cut-off tail | | VDD, GND, SWDIO, SWDCK, nRESET (5 pads) |
| BT1 | 3 V cell, see below | | Hand-fitted underneath with conductive epoxy, as on Irulu |

**GPIO budget** (QFN24 has 12 GPIOs):

| Signal | GPIOs |
|---|---|
| SPI SCLK / MOSI / MISO | 3 |
| CS_ACC, CS_BARO | 2 |
| ACC_INT1 | 1 |
| BARO_PWR | 1 |
| LIGHT (ADC) | 1 |
| SWD (on its own pins, shared with GPIO) | 2 |
| **Total** | **10** |

That leaves 2 spare, for example a status LED. Fix the pin numbers against the datasheet's RGE pinout in the
schematic.

## Mass (≤ 0.5 g target)

**Parts are 76–105 mg** (the CC2340 ≈ 25–35, the 100 µF C1 ≈ 23, ADXL367 + BMP581 ≈ 12–17, solder 8–12). The
body is assumed to be a Ø 8.5 mm disc (57 mm²), so a 6.8 mm cell fits underneath. Estimates include 20–40 mg of
epoxy and the antenna.

| Board | Board mg | Tag, no cell | + MS414GE (0.08 g) | + CR632 (0.20 g) | + MS621FE (0.23 g) | + CR816 (0.25 g) | + CR1025 (0.60 g) |
|---|---|---|---|---|---|---|---|
| FR4 0.6 mm | 79–89 | 0.177–0.238 | 0.26–0.32 ✓ | 0.38–0.44 ✓ | 0.41–0.47 ✓ | 0.43–0.49 ✓ | 0.78–0.84 ✗ |
| FR4 0.4 mm | 58–68 | 0.156–0.217 | 0.24–0.30 ✓ | 0.36–0.42 ✓ | 0.39–0.45 ✓ | 0.41–0.47 ✓ | 0.76–0.82 ✗ |
| **Flex + PI stiffener** | 23–28 | **0.123–0.180** | 0.20–0.26 ✓ | **0.32–0.38 ✓** | 0.35–0.41 ✓ | 0.37–0.43 ✓ | 0.72–0.78 ✗ |

**Every 3 V cell up to 0.25 g keeps the tag under 0.5 g, even on today's 0.6 mm FR4.** Flex buys about 60 mg of
margin, which the attachment (glue, a collar) will use. A CR1025 (30 mAh) breaks the limit, but at ≈ 0.75 g it is
still an option for bats over 15 g.

## Battery life

| Scenario | Avg | MS414GE (2 mAh) | CR632 (13 mAh) | MS621FE (5.5 mAh) | CR816 (8 mAh) | CR1025 (30 mAh) |
|---|---|---|---|---|---|---|
| Bat default: 50 Hz, advert 5 s | 6.6 µA | 13 d | 83 d | 35 d | 51 d | 191 d |
| Moth wingbeat: 100 Hz, advert 5 s | 8.9 µA | 9 d | 61 d | 26 d | 37 d | 140 d |
| Long life: 25 Hz, advert 10 s | 3.6 µA | 23 d | 149 d | 63 d | 91 d | 343 d |
| Bat default with DC/DC inductor | 5.7 µA | 15 d | 96 d | 41 d | 59 d | 221 d |
| Dense phones (2 s adverts), 50 Hz | 10.5 µA | 8 d | 52 d | 22 d | 32 d | 120 d |

These are lives to rated capacity at 20 °C; plan on ~70 % in the field.

**Where the current goes** in the bat default:

| Item | Current |
|---|---|
| Adverts | 2.6 µA |
| Draining the accelerometer FIFO | 2.3 µA |
| Accelerometer | 0.9 µA |
| Sleep | 0.7 µA |

Three numbers are **assumptions** to measure first on a CC2340 LaunchPad with a PPK2:

- the charge per advert (13 µC);
- the charge per FIFO drain (8 µC);
- the GLDO TX current.

**Sample rate:** the ADXL367's anti-alias filter attenuates wingbeats near ODR/4. Use 50 Hz for small bats
(wingbeats ≈ 8–15 Hz) and 100 Hz for hawkmoths (≈ 25–35 Hz).

## Burst: why C1 stays 100 µF

The table gives the minimum VCC during one 3-channel advert at an assumed 9 mA TX current. Effective capacitance is
taken as ≈ 45 % of nominal at 2.5–3 V. The floor is 1.9 V (both U1 and the BMP581 need 1.71 V).

| Cell state | 10 µF 0402 | 22 µF 0603 | 47 µF 0805 | 100 µF 0805 |
|---|---|---|---|---|
| fresh 3.0 V, 100 Ω | 2.22 | 2.38 | 2.59 | 2.77 |
| half 2.8 V, 150 Ω | 1.73 ✗ | 2.03 | 2.34 | 2.55 |
| late 2.5 V, 250 Ω | 1.02 ✗ | 1.58 ✗ | 1.98 | 2.24 |
| cold end 2.3 V, 400 Ω | 0.47 ✗ | 1.27 ✗ | 1.75 ✗ | 2.03 |

Small 3 V cells are 80–100 Ω fresh and climb toward 300–400 Ω cold and near empty. Below 100 µF the tag would brown
out in the second half of the cell's life.

## Cells (3 V)

| Cell | mAh | g | Size (mm) | Notes |
|---|---|---|---|---|
| MS414GE (Seiko) | 2.0 | 0.08 | 4.8 × 1.4 | Lightest. Rechargeable, so charge before fitting. Short life |
| **CR632** | 13 | 0.20 | 6.8 × 3.2 | Best capacity per gram, **but the data comes from one Chinese supplier's table**: buy samples, weigh them, and load-test them on a PPK2 |
| MS621FE (Seiko) | 5.5 | 0.23 | 6.8 × 2.1 | Well documented, 80 Ω. The safe first choice |
| CR816 | 8 | 0.25 | 8.0 × 1.6 | Same caveat as CR632. The thinnest |
| CR1025 | 30 | 0.6 | 10 × 2.5 | Over the 0.5 g budget |

**For the first boards:** design the underside for a **6.8 mm cell**, which takes both the MS621FE and the CR632.
Keep Irulu's crimp keep-out logic and the − pad at the centre. Bench-test both cells.

## Shared mechanical interface: rigid and flex

The flex version doesn't need the rigid layout, but **the cell tab and the antenna keep the same positions**. Then
finishing, attachment and RF comparisons carry over between versions. Coordinates follow the existing tags: origin
at the cell centre, x right, y down, top view.

| Feature | Position | Rigid | Flex |
|---|---|---|---|
| Cell − contact | centre, Ø 2.0 mm mask opening | conductive epoxy, as Irulu | the same, on a PI stiffener |
| **Cell + tab** | rim at **−55°** (upper right, Irulu's + pad angle) | + pad, wire to the can | **fold-over tab** 1.2 mm wide from the rim, folded down onto the can wall and silver-epoxied |
| **Antenna feed** | rim at **−19°** (Irulu's AE1) | wire pad, λ/4 ≈ 31 mm wire | **printed trace** leaving the rim radially at −19°: a 0.5 mm-wide strip with a λ/4 trace, trimmed to length |
| Counterpoise (optional) | rim at **147°** (Irulu's AE2) | wire pad | printed GND strip |
| Programming tail | **+90°** (bottom), cut after programming | 5 SWD pads | the same, on a stiffener for pogo pins |
| BMP581 vent | top face, away from the tail | | |

These numbers go into one shared constants file when the KiCad generator for this tag is written. It will be a copy
of `irulu/tools/design.py`, and the rigid and flex boards will both read from that file.

## Firmware

- **[`firmware/core/`](firmware/core/)** is the platform-independent part, in C99 with host tests:
  - VeDBA integrator;
  - activity minutes and alive/dead;
  - hourly bins for the 24 h minima;
  - payload packer.
- **Still to write: the platform layer**, on the TI SimpleLink Low Power F3 SDK with the Hubble TI toolkit:
  - RTC minute tick;
  - ADXL367 FIFO watermark interrupt → SPI drain → `gantu_accel_push()` per sample;
  - every 5 min: power the BMP581, take a one-shot reading, read the light ADC and the battery monitor, then
    `gantu_env_sample()`;
  - every payload period: `gantu_pack_payload()` → `hubble_ble_advertise_get()` → advertise.

**Decoders:** [`tools/gantu_payload.py`](tools/gantu_payload.py) (Python) and
[`R/decode_gantu_payload.R`](R/decode_gantu_payload.R) (R). Both are checked against the C encoder on 408 simulated
payloads.

## Open items, in order

1. **Hubble on the CC2340R52** (36 KB RAM):
   - confirm the TI toolkit fits;
   - check what TI's "max 1,024 advertisements per day" means: payload updates or transmissions? It sets the
     payload refresh period.
2. **PPK2 measurements on a CC2340R5 LaunchPad** with ADXL367 and BMP581 breakouts, to replace the three
   assumptions above.
3. **Cells:** buy CR632 and MS621FE samples; weigh them; measure impedance at 20 °C and 5 °C.
4. **ADXL367 supply at JLC:** consign the part, or fall back to a part JLC stocks (LIS2DU12 or BMA400; both need
   ≥ 1.62–1.72 V, which a 3 V cell gives).
5. **Schematic and layout** from TI's CC2340R5 RGE reference design: crystal, decoupling, RF filter.
6. **Antenna:** RSSI A/B, wire vs printed trace, before and after epoxy.
