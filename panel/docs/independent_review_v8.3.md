# Independent pre-order review, v8.3 combined panel (6 Nov 2026)

A separate agent checked the order files from scratch: the panel, Gerbers, drill, BOM, CPL and both `design.py` files,
against datasheets and JLCPCB's capability pages. It did not see the design notes. Its scripts and renders are in the
build session's scratchpad (`review83/`).

**Verdict:**
- No file defect would get the order rejected, and nothing makes a whole design or variant fail for certain.
- Connectivity, BOM, CPL, per-variant population and paste removal were all correct.
- Below: each finding and what was done about it. Findings marked *applied* changed the files.

## Findings and resolutions

### B1 (blocker only if stock is short): C1 100 µF 0805, C141660, 36 needed
- **Finding:** LCSC's shop shows it out of stock.
- **Resolution:** JLC's assembly library shows 143,099 (parts database, 6 Nov). The README says to confirm in the cart,
  and lists two fallbacks: Taiyo Yuden JMK212BBJ107MG-TE (C2880375, 5,627) and CCTC C49215609 (9,895).
- TPS3831G18DQNR has 57 in JLC's library (16 needed); IN100 has 703 (36 needed).

### S1: IN100 exposed-pad paste sat over the four thermal vias (*applied*)
- **Finding:** each paste window covered a 0.3 mm via, whose barrel can swallow that window's solder. This risks a
  starved exposed-pad joint, and the exposed pad is the IN100's only GND connection.
- **Applied:** the paste is now a cross through the centre: 1.3 × 0.34 mm plus 0.24 × 1.5 mm. Every aperture edge is
  ≥ 0.13 mm from a via drill.
- **D1 only:** the two upper vias lie inside the − pad's 2.0 mm mask opening, so some solder may show there as a small
  bump. This is harmless under silver epoxy.

### S2: TPS3831 X2SON paste was 1 : 1 with pads 0.141 mm from the thermal pad (*applied*)
- **Finding:** any bridge there kills the S tags.
- **Applied:** paste margin −0.04 mm on all five pads, giving 0.38 × 0.23 mm on the pins, close to TI's stencil example.
  Copper is unchanged.

### S3: HASL on a 0.4 mm-pitch QFN, a 1 × 1 mm X2SON and a thin slotted panel
- **Finding:** HASL leaves uneven pads and dips the thin panel in hot solder.
- **Resolution:** the README recommends **ENIG**; HASL is allowed at 0.6 mm.

### S4: VCC and GND crossed the CUT line only 0.15 mm apart, and D1 V2 is cut with the cell live (*applied*)
- **Applied:** neck tracks spread apart. At the cut line:
  - D2: GND–VCC 0.40 mm.
  - D1: EN–GND 0.31 mm, GND–VCC 0.295 mm.
- **Procedure added:** score and snap (or file) at CUT, never side cutters, then check VCC–GND.

### S5: unfitted pads were bare tinned copper next to pasted pads (*applied*)
- **Applied:** `mixed_variants.py` now removes both the paste and the mask opening from every pad of a part the unit
  doesn't fit:
  - R1 on S6/S6L;
  - U2, D2 and R2 on N6.

### S6: D2 side break-out tabs sat beside C1 (0805, across the break line), U2 and the crystal (*applied*)
- **Applied:** the D2 body side tabs are removed. The body hangs from its far-end tab and the neck, and the tail is held
  on three sides.
- **Procedure added:** cut the body tabs; don't snap them.
- D1's side tabs stay: its parts lie parallel to the break lines.

### S7: variants indistinguishable once the tails are cut (*applied*)
- **Applied:** each body's underside now carries its variant: S6 / S6L / N6 at 1 mm high on D2, and V1 / V2 between the
  cell outlines on D1.

### S8: stale documents (*applied*)
- **Applied:**
  - V2's bridged current corrected to 15.5 µA in the README and the JP1 note.
  - Ordering README written: Standard PCBA, Different Design in Panel = 2, 0.6 mm, mark location.
  - The single-tag READMEs now point to it.

### Notes
- **N1.** Copper sits exactly at JLC's 0.20 mm from edges and mouse-bite holes. Expect a DFM comment, not a rejection.
- **N2.** Silk text is 0.4–0.7 mm, below JLC's recommended 1 mm, so it may blur.
- **N3.** The drill file mixes plated and unplated holes. The 0.5 mm mouse bites and 1.152 mm tooling holes are
  unplated.
- **N4.** Other different-net pad gaps of 0.14–0.20 mm are all on fitted parts with mask webs. One case: C4 to IN100
  pin 14 (RTC_XO_P, absolute maximum min(2 V, VCC)) would be over-stressed by a bridge during 3.3 V programming.
  Inspect it under magnification.
- **N5.** A thin 95 × 71 mm panel may sag in reflow; JLC may add a carrier.

## Circuit points from the review, adopted in the bring-up notes
- **D2 hold times:** about 0.55 s (S6) and 1.7 s (S6L) for CHIP_EN to fall to 0.6 VCC. RB751 leakage in warm sun
  (≈ 0.2–0.5 µA at 45–55 °C) shortens both.
- **D2 start:** the start-to-brown-out budget is ≈ 32–50 µC, enough for one advert but not two.
- **D2 programming:** program S tags at 0 dBm or lower; one advertising channel is better.
- **D1 V2:** a sensible hedge against an internal CHIP_EN pull-down down to ≈ 150 kΩ.
  - **CHIP_EN load test:** measure EN on JP1 with a 10 MΩ meter. Expect ≈ 0.91·VCC on V1 and ≈ 0.99·VCC on V2.
- **D1 brown-out lock:** recover by shorting C1 for about 1 s.
- **Test before cutting:** program and check every tag on the panel through J1.

## Checked and found correct (summary)
- **Panel:**
  - 94.8 × 71.0 mm, one outline, 5 mm frame, backbone 12.1 mm.
  - 3 + 3 fiducials, 4 tooling holes (1.152 mm), 2 mm gaps.
  - Mouse bites 0.5 mm at 0.75 mm.
  - Tracks and gaps ≥ 0.13 mm; vias 0.5/0.3 mm.
  - Bottom paste empty. Gerber job says 0.6 mm. Zip identical to the Gerber folder.
- **Connectivity:** all 18 units match their `design.py` NETS; no shorts or unconnected pads.
- **BOM/CPL:**
  - 184 placements, each designator once.
  - Values and LCSC numbers per variant correct.
  - CPL X/Y/rotation match the panel.
  - Row-2 rotations = row 1 + 180°.
  - Every paste flash lands on a fitted pad.
- **Parts and footprints:** IN100, crystal, C1, TEMD7000X01, RB751S40, TPS3831 and 100 kΩ confirmed against their
  datasheets. The IN100 footprint matches the package drawing.
- **Hand finishing:**
  - D2 underside antenna pads: ≥ 3.3 mm to any other pad.
  - D1 AE1: ≥ 0.75 mm. D1 AE2: 0.39–0.44 mm.
  - Crimp keep-out holds.
  - J1 labels match the nets.

## Placement-preview checks (from the review)
- **U1:** pin-1 dot next to the crystal: upper left on upright tags, lower right on the 180° row.
- **Y1:** no silk mark; judge by copper. Pads 1 and 3 (XO) are on one diagonal. 180° is harmless; **90° is fatal**.
- **U2:** pin 1 (RESET, chamfered pad) at the dot.
- **D2:** cathode band towards C5/R2.
- **Photodiodes:** cathode at the silk bar. In row 1, PD1, PD2, PD5 and PD6 have the cathode on the left and PD3, PD4 on
  the right. One reversed photodiode stops the string.
- Judge photodiode polarity by pad position: the outer silk bars sit on the board edge and may be trimmed.
