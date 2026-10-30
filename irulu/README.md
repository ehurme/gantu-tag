# IN100 insect tag v5 (8 mm round, wire antenna)

This is an open Bluetooth LE beacon tag for insects, built around the InPlay **IN100 NanoBeacon**.
You choose **Hubble** or Apple **Find My** (OpenHaystack-style keys) when you burn the IN100's OTP.
JLCPCB fits all four parts from its own stock, all on the top side. You add the 337 cell underneath, a 30 mm wire and epoxy.
A programming tab hangs off a neck, and you cut the neck once the tag is programmed.

![KiCad 10 3D render](docs/pcb_3d_kicad10.png)

## What changed from v4

| | v5 (this) | v4 |
|---|---|---|
| IN100 package | **QFN18, IN100-Q1-R-RC1I, JLC/LCSC C6062024 (in JLC stock)** | DFN8, not stocked by JLC (Global Sourcing) |
| Bulk capacitance | **one 100 µF 0805** (≈ 80 µF effective at 1.5 V) | 10 µF: too small for a 337 cell |
| Antenna | 30 mm enamelled wire in a plated hole | 30 mm trace on an FR-4 arm |
| Tag | 8 mm round, 0.6 mm FR-4; about 3.6 mm tall with the cell | 6.4 mm round + 30 mm arm |
| Panel | **20 tags**, 98 × 47 mm | 12 tags, 92 × 89 mm |
| 3D models | every part, stored in the project | IN100 and crystal missing |

### Why the big capacitor matters

A 337 (SR416SW) is a low-drain silver-oxide cell with an internal resistance of about **80 Ω** (Energizer: 75–85 Ω at 40 Hz).
Its resistance rises in the cold and as the cell runs down.
The IN100 draws **9.1 mA** while transmitting at 0 dBm and **13.8 mA** at +5 dBm (datasheet Table 19), and needs at least **1.1 V**.
On its own the cell would drop to about 0.8 V during every transmission, so a capacitor has to carry each advertising burst.

`tools/burst_sim.py` models one advertising event: crystal start-up, then three channels of about 0.5 ms each.
It reports the lowest supply voltage the IN100 sees during the event:

| Bulk capacitance | Fresh cell (80 Ω) | Cold or half used (150 Ω) | Nearly flat (250 Ω) |
|---|---|---|---|
| 10 µF (v4), 0 dBm | 0.92 V ✗ | 0.56 V ✗ | 0.25 V ✗ |
| 3 × 22 µF 0402, 0 dBm | 1.31 V | 1.26 V | 1.21 V |
| 3 × 22 µF 0402, +5 dBm | 1.20 V | 1.14 V | 1.09 V ✗ |
| **100 µF 0805 (v5), 0 dBm** | **1.38 V** | **1.35 V** | **1.31 V** |
| **100 µF 0805 (v5), +5 dBm** | **1.30 V** | **1.26 V** | **1.22 V** |

With the 100 µF capacitor, **anything up to +5 dBm works for the whole life of the cell.** Keep the **1 Mbps PHY**:
the 125 kbps coded PHY transmits for about 8× longer per packet and would need far more capacitance.
C2 is a Murata GRM21BR60J107ME15L, 100 µF 6.3 V X5R 0805 (LCSC C141660), 2.0 × 1.25 × 1.25 mm. The simulation assumes it loses about 20 % to DC bias at 1.5 V.
It sits at 45° at the lower left, the only place on the round tag long enough for it. C1 is 100 nF (C1525) right at the VCC pin.

### Battery life (estimate)

These figures assume about 16 µC per advertising event at 0 dBm and 0.625 µA sleep current.
They ignore self-discharge and the cell's rising resistance near the end, so treat them as upper bounds.

| Advertising interval | 1 s | 2 s | 5 s | 10 s | 60 s |
|---|---|---|---|---|---|
| Average current | 17 µA | 8.7 µA | 3.9 µA | 2.2 µA | 0.9 µA |
| Life on 8.3 mAh | ~3 weeks | ~6 weeks | ~3 months | ~5 months | ~1 year |

![board](docs/pcb_preview.png)

## Circuit

- **U1 IN100 (QFN18)** runs straight off the cell (1.1–3.6 V).
  - CHIP_EN, VCC and VDDQ are tied together.
  - The UART is on GPIO0 (RXD) and GPIO1 (TXD).
  - The other GPIOs, the two load switches and the RTC crystal pins are left open; the internal 32 kHz RC oscillator is used.
- **CHIP_EN** is tied straight to VCC. InPlay's and SparkFun's reference designs put a 10 kΩ/100 nF (1 kΩ on SparkFun's) RC on it, which gives a reset button and a short enable delay.
  On this tag the supply already rises slowly through the cell's resistance and the 100 µF capacitor (τ ≈ 8 ms), and the IN100 has its own power-on reset, so the RC would add little.
- **Y1** TXC 8Q26000008: 26 MHz, 7 pF, ±16 ppm, 1.6 × 1.2 mm (C5203638). The IN100's on-chip load capacitors replace external ones.
- **AE1** is a plated hole (0.4 mm drill) for about 30 mm of fine enamelled wire, which is a quarter wave at 2.44 GHz. It's fed straight from RF_TX.
- **BT1:** a bare gold **Ø2 mm pad on the underside**, centred on the cell's negative cap, takes a dot of silver epoxy. Two top rim pads take the + wire, or welded tabs if you prefer: **+ at the top**, **− at the right**.
- **J1** is on the cut-off tab: **R** = RXD (into the IN100), **T** = TXD (out of the IN100), **+** = VCC, **G** = GND, on a 2 × 2, 2.54 mm grid.

Layers: every part is on the top. The bottom is a ground plane with the VCC traces, and it sits flat against the cell.
Apart from the central epoxy pad, **keep Kapton between the board and the cell**: the cell's can is +, and the ground plane under the solder mask is −.
The neck carries RXD, GND and TXD on top and VCC alone underneath, so a copper burr from cutting can't easily short the supply.

## What's in the folder

| Path | What it is |
|---|---|
| `insect_tag.kicad_pro`, `.kicad_sch`, `.kicad_pcb` | KiCad project (KiCad 7 format; checked in KiCad 10.0.7) |
| `insect_tag.kicad_sym`, `insect_tag.pretty/`, `insect_tag.3dshapes/` | IN100 QFN18 symbol, footprints and 3D models |
| `fab/jlcpcb_panel/` | **What you upload to JLCPCB**: Gerbers zip, BOM and CPL |
| `fab/jlcpcb_single/` | Gerbers for one tag + tab (bare boards for hand assembly) |
| `docs/` | Schematic PDF, board render, KiCad 3D render, panel render, DRC report |
| `tools/` | Generators (`design.py` holds every part, placement and track), `burst_sim.py`, KiKit panel config, `make_fab.sh` |

## Ordering from JLCPCB

1. Upload `fab/jlcpcb_panel/insect_tag_panel_gerbers.zip`. Options:
   - 2 layers, **0.6 mm** thickness, ENIG recommended (the QFN has a 0.4 mm pitch).
   - Delivery format **Panel by Customer**. The rails, tooling holes and fiducials are in the Gerbers.
   - For "Mark on PCB", specify the location: the bottom rail carries a `JLCJLCJLCJLC` marker.
2. Turn on PCB Assembly, top side. Upload `insect_tag_panel_bom.csv` and `insect_tag_panel_pos.csv`.
   - All four line items have LCSC numbers.
   - U1 (C6062024), Y1 (C5203638) and C2 (C141660) are **extended** parts. C1 is basic.
3. In the placement preview, check that the pin-1 marks on **U1** and **Y1** match the silkscreen dot and the board, and that **C2** sits at 45° on its pads.

![panel](docs/panel_top.png)

## Bringing up a tag

**Program first, fit the cell last. Never connect the programmer while a cell is fitted.**

1. **Break a tag out of the panel.** Snap the tabs and sand the nubs. Leave the neck intact.
2. **Wire a 3.3 V USB-UART adapter** to the tab's pads, using a pogo jig, a 2 × 2 header or tacked wires:
   - **T** → adapter RX
   - **R** → adapter TX
   - **G** → GND
   - **+** → 3.3 V

   Use 3.3 V because VDDQ needs it (up to 50 mA) while the OTP is burned.
3. **Program with InPlay's NanoBeacon Config Tool.**
   - Load the configuration into RAM first and check it with a phone scanner, then burn the OTP. **The OTP can be written only once.**
   - Set TX power to **+5 dBm or lower**, keep the **1 Mbps** PHY, and use an interval of 1 s or longer.
   - *Hubble:* follow Hubble's IN100 guide.
   - *Find My (OpenHaystack-style):* non-connectable advertising with the payload `1E FF 4C 00 12 19 00 <key bytes 6–27> <key[0] >> 6> 00`.
     The static random address is `key[0] | 0xC0, key[1..5]`.
4. **Cut the neck** at the silkscreen line, flush to the tag, with sharp flush cutters. Sand the stub.
5. **Check for shorts:** measure across the + and − rim pads. You should see the 100 µF charging, not a dead short. Measure again once the cell is fitted: you should read about 1.55 V.
6. **Antenna:** strip about 0.5 mm of a ~0.1 mm enamelled copper wire. Push it through the hole by RF_TX, solder it, and trim the wire to 30 mm.
   Trimming shortens it and raises its resonant frequency. Epoxy lowers it.
7. **Fit the cell with silver epoxy** (no soldering on the cell, no welded tabs). The cell's small raised cap (−) faces the board and the can (+) faces away.
   - Punch a **Kapton washer** with a ~2 mm hole and stick it on the underside, the hole over the gold pad. The bottom silkscreen ring shows where the cell sits.
     The washer covers the cell's crimped rim, which is +.
   - Put a **small** dot of two-part silver epoxy on the gold pad, then press the cell on, centred in the ring.
     **The cap and the can are only a fraction of a millimetre apart. Epoxy that bridges them shorts the cell.**
   - **+:** tack a short piece of thin wire or 0.1 mm nickel strip to the can's side wall with silver epoxy, and solder its other end to the **+** rim pad at the top.
   - Hold the stack together while the epoxy cures at room temperature, with a clip, a friction-fit collar or a small clamp. Don't heat the cell above its 60 °C rating.
     A friction fit alone isn't reliable in the field, because vibration and temperature changes loosen it. Once the silver epoxy has cured, add a structural-epoxy fillet around the cell's edge.
   - *Alternative:* use a cell with welded tabs on the two rim pads (+ top, − right), with a full Kapton disc that also covers the gold pad.
8. **Coat** the tag and cell in a thin layer of structural epoxy. Leave the antenna wire free beyond the first millimetre.

## Mass (estimate)

| Part | Mass |
|---|---|
| Board, 8 mm × 0.6 mm FR-4 | 56 mg |
| Copper, mask and finish | ~29 mg |
| IN100, crystal, 100 nF, solder | ~27 mg |
| 100 µF 0805 capacitor | ~17 mg |
| Antenna wire (30 mm, 0.1 mm) | ~2 mg |
| 337 cell (0.13 g) | 130 mg |
| **Total before epoxy** | **≈ 0.26 g** |

Height: cell 1.65 mm + Kapton and epoxy dot about 0.1 mm + board 0.6 mm + capacitor 1.25 mm (the tallest part) ≈ **3.6 mm** before the epoxy coat.
A 0.4 mm board saves about 18 mg and 0.2 mm, but JLC treats 0.4 mm as special (no HASL, manual review). Weigh your first tags rather than relying on these numbers.

## Checks done

- **KiCad 7.0 DRC** (the build tools): 0 violations, 0 unconnected; the board netlist matches the design.
- **KiCad 10.0.7 DRC** (after a zone refill): 0 errors, 0 warnings, 0 schematic-parity issues.
  **KiCad 10.0.7 ERC**: 0 errors, plus 2 cosmetic warnings about library-copy differences in the embedded crystal and battery symbols.
- JLC standard rules throughout: tracks and gaps ≥ 0.13 mm, 0.3 mm vias, copper ≥ 0.2 mm from the edge.
  The only finer feature is the QFN's own 0.4 mm pin pitch, with 0.2 mm pads and 0.2 mm gaps.

## Before you order a batch

- **QFN18 land pattern:** built from InPlay's package drawing (datasheet v1.3, Figure 22). Compare it with the LCSC/JLC footprint preview before ordering.
- **Crystal land pattern:** the 1612 pads (0.6 × 0.5 mm on a 1.05 × 0.75 mm grid) come from the NDK NX1612SA layout. Check them against TXC's 8Q drawing.
- **Sleep current:** large ceramic capacitors are specified for leakage only loosely, up to a few µA at worst. Real parts at 1.5 V usually leak far less.
  Measure one finished tag's average current: if it's well above about 1 µA between advertisements, the capacitor is the cause.
- **RF and battery life** are estimates; nothing here has been tested on air yet. **Order one panel and bring up one tag end to end before you order more.**

## Rebuilding

- `tools/design.py` holds the parts, nets, outline, placement and every track and via.
- `tools/gen_footprints.py` writes the footprints and 3D models.
- `tools/build.py` writes the KiCad files, `tools/check.py` runs DRC and a netlist check, and `tools/render.py` draws the previews.
- `tools/make_fab.sh` rebuilds the panel and JLC files and needs [KiKit](https://github.com/yaqwsx/KiKit).

## License

CC BY-SA 4.0. The IN100 circuit references were InPlay's IN100 datasheet and SparkFun's NanoBeacon boards (CC BY-SA 4.0).
No warranty: you build and use these at your own risk.
