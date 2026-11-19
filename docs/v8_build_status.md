# v8.3 build status (6 Nov 2026)

Follows [`v8_handover.md`](v8_handover.md). **v8.3 is the revision that was ordered:** both tags on one 0.6 mm
combined JLCPCB panel. D1 is Irulu (battery), D2 is Hagalu (solar). The D3 sensor tag from the handover is paused.

## The order

- **Panel:** 94.9 × 71.1 mm, 2 layers, **0.6 mm**.
  - **Standard PCBA**: Economic only takes 0.8–1.6 mm, and Standard needs a panel of at least 70 × 70 mm.
  - Panel by Customer, **Different Design in Panel = 2**, PCB qty 5, **PCBA qty 2**.
  - ENIG recommended; HASL is allowed at 0.6 mm.
- **Per panel:**
  - D2 (Hagalu): S6 ×4, S6L ×4, N6 ×2.
  - D1 (Irulu): V1 ×4, V2 ×4.
  - Two assembled panels → 36 tags, plus 54 bare boards.
- **Rough cost:** €250–280 before shipping, about €7 per tag; the BOM dominates.
- **Stock (JLC database, 6 Nov):**

| Part | LCSC | Stock | Need |
|---|---|---|---|
| IN100 | C6062024 | 703 | 36 |
| C1 | C141660 | 143,099 | 36 |
| TEMD7000 | C145328 | 2,315 | 120 |
| TPS3831G18DQNR | C2066667 | 57 | 16 |

C1 fallback: C2880375 (Taiyo Yuden) or C49215609.

## What changed from v8.2

- **D2 antenna pads moved to the underside** (no parts there): two 1.2 × 1.0 mm edge pads, with a via in the AE1 (RF)
  pad. The underside VCC trunk was rerouted.
- **D1 antenna pads:** AE1 moved to the upper-right rim (1.2 × 0.9 mm, ≥ 0.75 mm to other-net pads); AE2 is a slim
  0.5 × 0.9 mm pad, 0.36 mm clear.
- **D1 V2 = 100 kΩ / 10 nF:** a hedge against an unpublished CHIP_EN pull-down or input current, which would kill every
  1 MΩ enable. Cost: 15.5 µA while OFF is bridged (a 337 lasts ≈ 22 days bridged).
- **Paste and mask:** IN100 exposed-pad paste is a centre cross clear of the thermal vias; TPS3831 paste is 0.04 mm
  inside its pads; unfitted parts are masked over with no paste.
- **Panel tabs:** D2 body side tabs removed (C1 and U2 sit 0.2 mm from the edges); tails held by wide tabs.
- **CUT line:** underside VCC, GND and EN tracks across it spread to D2 0.40 mm, D1 ≥ 0.29 mm (was 0.15).
- **Labels:** the variant is printed on each body's underside.

## Checks done before ordering

- KiCad 7: both tags and the panel DRC 0/0; netlist parity; Gerbers rendered and inspected.
- KiCad 10.0.7: DRC 0 errors on the panel and both tags; ERC 0 errors. Only cosmetic warnings.
- **Independent pre-order review** by a separate agent: no blocker; its suggestions S1–S8 were applied. See
  [`../panel/docs/independent_review_v8.3.md`](../panel/docs/independent_review_v8.3.md).

## Still open (bench, before burning OTP on many tags)

- CHIP_EN load test on V1/V2 (EN at JP1 with a 10 MΩ meter).
- First-advert latency and CHIP_EN turn-off (settles S6 vs S6L).
- C1's real capacitance and the D1 burst dip.
- N6's power-on behaviour.
- Sunlight vs LED calibration.
- **Next revision:** flex or 0.4 mm for mass, once these tags have settled the start circuit.
