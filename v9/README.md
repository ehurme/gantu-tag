# v9 KiCad projects

Open the `.kicad_pro` in KiCad 10. Each project has a schematic, a PCB with a removable programming tail, and local symbol, footprint and 3D model files. The tails use Ø0.95 mm surface pads on 1.80 mm pitch. The [v8.3 bench checklist](../docs/roadmap.md#stage-0-bench-work-on-the-v83-boards-now) controls the remaining PCB decisions. The v9 project files are their own source. The v8 generators still target the pilot boards.

| Project | Saved PCB draft | Before fabrication |
|---|---|---|
| [Hagalu S6 flex](hagalu/hagalu_v9_s6.kicad_pro) · [render](renders/hagalu-s6.png) | 6.55 × 13.68 mm body, with a 6.32 mm-wide photodiode section and nominal 0.11 mm polyimide stackup. The tail has VCC and CHIP_EN probe pads beside the programming pads. | Qualify the ½ oz copper stackup, radio and crystal stiffener, and supported pogo contacts. Design the hatched ground and the printed-trace trial alongside the glued 0.10 mm wire reference. Use bench data to decide on the 47 µF C1 and alternate photodiode counts. |
| [Irulu 337](irulu-337/irulu_v9_337.kicad_pro) · [render](renders/irulu-337.png) | Ø6.75 mm circular body with underside contacts for a 4.8 mm 337 (SR416). The QFN18 and 0402 decoupling capacitor are retained. The v8.3 V1 enable is the reference at 0 dBm on one network. | Choose V1 or V2 after measuring CHIP_EN and qualify the rim contact and insulation. Choose rigid or flex for mechanical support. The saved PCB uses the default 1.6 mm thickness as a placeholder. Confirm custom panelization for this size with the fab. |
| [Irulu larger cell](irulu-large-cell/irulu_v9_large_cell.kicad_pro) · [render](renders/irulu-larger-cell.png) | Ø10.00 mm circular body on a 0.6 mm rigid draft. The negative contact is underneath and the positive strap pad is on top. | Choose the exact 7.9–9.5 mm cell, insulate the positive pad from the can, and verify contact support and startup. Qualify the +4 dBm, three-network profile on the bench. |

## Hagalu light-sensing trial

All seven photodiode footprints use Vishay's TEMD7000X01 land pattern, with 1.00 × 1.45 mm pads and a 0.60 mm gap. [Vishay TEMD7000X01 datasheet, page 4](https://www.vishay.com/docs/81951/temd7000.pdf#page=4)

PD7 is a separate photovoltaic sensor. R3 loads it to ground and R4 limits current into U1 pin 5 (MGPIO5, ADC channel 1). PD7, R3 and R4 are marked DNP. Fit them together for the trial and check the ADC reading in RAM, the input with VCC off, and the effect on cold startup. R3 and R4 are provisional 100 kΩ values. InPlay limits VCC to 3.0 V for external analog measurements. Keep the 3.3 V programming session separate from ADC measurements. [InPlay IN100 datasheet, tables 1 and 2 and §4.4.3](https://www.inplay-tech.com/IN100_datasheet.pdf)

The QFN18 exposes the light-sensing input while retaining RXD and TXD. The DFN8 pins that could otherwise serve as analog inputs are assigned to UART in that package. Keep the QFN18 for this Hagalu draft and qualify DFN8 separately for Irulu. [InPlay IN100 pin assignments](https://www.inplay-tech.com/IN100_datasheet.pdf#page=12)

## Check the projects

The paired renders show the top and underside of each saved layout. Recreate them with `sh v9/render.sh` from the repository root using KiCad 10 and ImageMagick. Set `KICAD_CLI` if KiCad is installed in a custom location.

Run `sh v9/check.sh` after each change. It checks schematic ERC, PCB design rules, unrouted connections and schematic parity on all three projects. Pass a report directory as the first argument to retain the JSON reports there. Hagalu uses 0.30 mm copper-to-edge clearance for the flex outline. The other rules and net classes inherit the v8.3 defaults. Confirm the selected fabrication rules and stackups before releasing any board. [JLCPCB flex capabilities](https://jlcpcb.com/capabilities/flex-pcb-capabilities/)

Run `python3 v9/check-tail.py` with KiCad's `pcbnew` Python bindings to check Hagalu and Irulu 337 after simulated tail removal. On macOS, use `/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3.9` if the system Python lacks the bindings. The script clips copper in temporary copies at each board's neck and checks the surviving connections.
