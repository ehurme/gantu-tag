# v9 KiCad projects

Open the `.kicad_pro` in KiCad 10. Each project has a schematic, a placed PCB draft with a removable programming tail, and local symbol, footprint and 3D model files. The [v8.3 bench checklist](../docs/roadmap.md#stage-0-bench-work-on-the-v83-boards-now) controls the remaining PCB decisions. The v9 project files are their own source. The v8 generators still target the pilot boards.

| Project | Saved PCB draft | Before fabrication |
|---|---|---|
| [Hagalu S6 flex](hagalu/hagalu_v9_s6.kicad_pro) · [render](renders/hagalu-s6.png) | 7 × 14.6 mm body, nominal 0.11 mm polyimide stackup, 22 footprints, and series routes between the six harvest photodiodes. The tail has VCC and CHIP_EN probe pads beside the provisional programming connector. | Qualify the ½ oz copper stackup, radio/crystal stiffener, and supported pogo contacts. Design the hatched ground and the printed-trace trial alongside the glued 0.10 mm wire reference. Use bench data to decide on the 47 µF C1 and alternate photodiode counts. |
| [Irulu 337](irulu-337/irulu_v9_337.kicad_pro) · [render](renders/irulu-337.png) | 6.36 × 6.5 mm body, 11 footprints, underside contacts for a 4.8 mm 337 (SR416), and a first VCC route. The v8.3 V1 enable is the reference at 0 dBm on one network. | Choose V1 or V2 after measuring CHIP_EN and qualify the rim contact and insulation. Choose rigid or flex for mechanical support. The saved PCB still uses the default 1.6 mm thickness as a placeholder. |
| [Irulu larger cell](irulu-large-cell/irulu_v9_large_cell.kicad_pro) · [render](renders/irulu-larger-cell.png) | 10.1 × 10.1 mm body, 0.6 mm rigid draft, 11 footprints and initial VCC routing. The large cell contact has a negative pad underneath and a positive strap pad on top. | Choose the exact 7.9–9.5 mm cell, insulate the positive pad from the can, and verify contact support and startup. Qualify the +4 dBm, three-network profile on the bench. |

## Hagalu light-sensing trial

PD7 is a separate photovoltaic sensor. R3 loads it to ground and R4 limits current into U1 pin 4 (MGPIO6, ADC channel 2). PD7, R3 and R4 are marked DNP. Fit them together for the trial and check the ADC reading in RAM, the input with VCC off, and the effect on cold startup. R3 and R4 are provisional 100 kΩ values. InPlay limits VCC to 3.0 V for external analog measurements. Keep the 3.3 V programming session separate from ADC measurements. [InPlay IN100 datasheet, tables 1 and 2 and §4.4.3](https://www.inplay-tech.com/IN100_datasheet.pdf)

The QFN18 exposes the light-sensing input while retaining RXD and TXD. The DFN8 pins that could otherwise serve as analog inputs are assigned to UART in that package. Keep the QFN18 for this Hagalu draft and qualify DFN8 separately for Irulu. [InPlay IN100 pin assignments](https://www.inplay-tech.com/IN100_datasheet.pdf#page=12)

## Check the projects

The paired renders show the top and underside of each saved layout. Recreate them with `sh v9/render.sh` from the repository root using KiCad 10 and ImageMagick. Set `KICAD_CLI` if KiCad is installed in a custom location.

Run ERC and DRC with schematic parity after each change. These drafts have partial routing. KiCad found no schematic-to-board mismatches on any of the three. Hagalu still needs clearance and mask checks at the U2 supervisor footprint. The projects inherit v8.3 rigid-board rules and net classes. Confirm the selected fabrication rules and stackups before releasing any board.
