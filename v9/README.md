# v9 KiCad projects

Open the `.kicad_pro` in KiCad 10. Each project has its own schematic, empty PCB, and local symbol, footprint and 3D model files. The schematics start from the v8.3 circuits. The [v8.3 bench checklist](../docs/roadmap.md#stage-0-bench-work-on-the-v83-boards-now) controls the PCB decisions. The v9 project files are their own source. The v8 generators still target the pilot boards.

| Project | Schematic | Before placement |
|---|---|---|
| [Hagalu S6 flex](hagalu/hagalu_v9_s6.kicad_pro) | Six harvest photodiodes, S6 enable with R2 at 3.3 MΩ, 100 µF C1, J1 with the provisional v8 footprint, and tail probe pads TP1 (VCC) and TP2 (CHIP_EN) | Qualify the 0.11 mm polyimide stackup, ½ oz copper, hatched ground and local radio/crystal stiffener. Choose the geometry and mechanical support for four pogo contacts. Keep a glued 0.10 mm wire as the reference and plan one printed-trace trial. Use bench data to decide on the 47 µF C1 and any alternate photodiode count. |
| [Irulu 337](irulu-337/irulu_v9_337.kicad_pro) | One 337 (SR416), 100 µF C1, and the v8.3 V1 enable values as a reference. Start at 0 dBm on one network. | Target a 6 × 6.5 mm body. Choose V1 or V2 after the CHIP_EN measurements and qualify the 4.8 mm cell contacts. Compare rigid and flex for contact support. |
| [Irulu larger cell](irulu-large-cell/irulu_v9_large_cell.kicad_pro) | A 7.9–9.5 mm cell placeholder, 100 µF C1 and the same enable reference. The +4 dBm, three-network profile is a bench target. | Choose the exact cell, provide an insulated positive pad and a strap to the can, and validate contact support and startup before assigning the battery footprint. |

## Hagalu light-sensing trial

PD7 is a separate photovoltaic sensor. R3 loads it to ground and R4 limits current into U1 pin 4 (MGPIO6, ADC channel 2). PD7, R3 and R4 are marked DNP. Fit them together for the trial and check the ADC reading in RAM, the input with VCC off, and the effect on cold startup. R3 and R4 are provisional 100 kΩ values. InPlay limits VCC to 3.0 V for external analog measurements. Keep the 3.3 V programming session separate from ADC measurements. [InPlay IN100 datasheet, tables 1 and 2 and §4.4.3](https://www.inplay-tech.com/IN100_datasheet.pdf)

The QFN18 exposes the light-sensing input while retaining RXD and TXD. The DFN8 pins that could otherwise serve as analog inputs are assigned to UART in that package. Keep the QFN18 for this Hagalu draft and qualify DFN8 separately for Irulu. [InPlay IN100 pin assignments](https://www.inplay-tech.com/IN100_datasheet.pdf#page=12)

## Check the projects

Run schematic ERC in KiCad after any change. At setup, all three schematics had zero errors and the same library-version warnings as their v8.3 references. The empty PCBs use KiCad's default 1.6 mm thickness, and the project files inherit the v8.3 rigid-board rules and net classes. Replace and verify these placeholders against the selected fabrication stackup and rules before synchronizing footprints, placing parts and running DRC.
