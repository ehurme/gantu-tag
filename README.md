<p align="center"><img src="docs/logo/gantu.svg" width="140" alt="gantu-tag logo: a trefoil knot shading from day ochre to night indigo"></p>

<h1 align="center">gantu-tag · ಗಂಟು</h1>

<p align="center"><b>Open, tiny Bluetooth LE tracking tags for insects that anyone can order from JLCPCB.</b></p>

*Gantu* (ಗಂಟು) is Kannada for a knot, and for the small bundle you tie up and carry. A tag is something you tie onto
an animal, so the logo is a knot whose thread runs from day to night.

These are **early pilots**. The first panel was ordered on 6 November 2026; nothing has been bench-tested yet.
Treat every number here as a design estimate until the bring-up results are in.

## The two tags

<p align="center"><img src="hagalu/docs/pcb_3d_top.png" width="300" alt="Hagalu Gantu, solar tag"> <img src="irulu/docs/pcb_3d_top.png" width="300" alt="Irulu Gantu, battery tag"></p>

| | **Hagalu Gantu** · ಹಗಲು ಗಂಟು (day) | **Irulu Gantu** · ಇರುಳು ಗಂಟು (night) |
|---|---|---|
| Power | Six photodiodes charge a 100 µF capacitor; no battery | A silver-oxide button cell (337, 364 or 377) |
| When it runs | **In light only**, in bursts as the capacitor fills | Day and night until the cell is flat (≈ 57 days on a 337 at a 3 s interval) |
| Size (after cutting the tail) | 6.4 × 12.55 mm | Ø 7.2 mm |
| Mass (design estimate, 0.6 mm board) | ≈ 0.19–0.21 g | ≈ 0.12 g without the cell, ≈ 0.25 g with a 337 |
| Start-up | On S6/S6L a supervisor starts the radio once the capacitor holds a burst; N6 has none | Fit the cell (V1), or cut the tail (V2) |
| Pilot variants on the panel | S6, S6L, N6 | V1, V2 |
| Design files | [`hagalu/`](hagalu/) | [`irulu/`](irulu/) |

Both use the InPlay **IN100 NanoBeacon**, a beacon chip configured rather than programmed. One tag works on Apple
**Find My** (OpenHaystack-style static key) or on **Hubble**, chosen when you burn its one-time-programmable memory.
You don't change the hardware to switch networks.

The pilot variant names (S6, S6L, N6, V1, V2) only mark the start-circuit options under test. They'll be narrowed
down once the first tags are on the bench.

## Build your own

1. **Order:** upload the files in [`order/`](order/). That folder holds the exact zip sent to JLCPCB, with the order
   settings and the placement checks. One order gives two assembled panels: 20 Hagalu and 16 Irulu tags.
2. **Program:** four wires from a 3.3 V USB-serial adapter to the tail, and InPlay's NanoBeacon Config Tool. See
   [`docs/programming.md`](docs/programming.md).
3. **Finish:** break the tag out, fit the antenna wire (and the cell on Irulu), cut the tail and coat it in epoxy.
   The step-by-step for each tag is in [`hagalu/README.md`](hagalu/README.md) and [`irulu/README.md`](irulu/README.md).

## Repository map

| Folder | What's in it |
|---|---|
| [`hagalu/`](hagalu/) | Solar tag: KiCad project, the Python that generates it (`tools/design.py`), solar simulation, renders, review |
| [`irulu/`](irulu/) | Battery tag: KiCad project, generator, burst simulation, renders, review |
| [`panel/`](panel/) | The combined 0.6 mm JLC panel (KiKit layout, mixed-variant BOM/CPL) and its ordering README |
| [`order/`](order/) | The exact files sent to JLCPCB, with a checksum |
| [`docs/`](docs/) | Programming guide, the v8 handover and build notes, the logo |

## History

Every revision is a commit, dated when it was made, and each released design has a git tag:

| Tag | What changed |
|---|---|
| `v4` | 6.4 mm round tag on a 0.6 mm board, printed antenna arm, cut-off programming tab |
| `v5` | 8 mm tag with a 30 mm wire antenna; all parts on the top side, cell underneath |
| `v6` | 7 mm tag with a Blu Bat-style **cut-to-start tail** (superseded: pour and decoupling faults, don't order) |
| `v7` | Fixes v6; any button cell; five population variants on one test panel |
| `v8.3` | Split into **Hagalu** (solar) and **Irulu** (battery) on one combined 0.6 mm panel. **This is what was ordered** |

Before v8 there was only the battery tag, so its history lives in `irulu/`. To see an old version, run
`git checkout v6`, for example.

## Licence

Hardware designs and documentation: [CC BY-SA 4.0](LICENSE). The designs reference InPlay's IN100 datasheet and
SparkFun's NanoBeacon boards (CC BY-SA 4.0). No warranty: you build and use these at your own risk.

Designed by Pavan Kumar Kaushik (Max Planck Institute of Animal Behaviour, Konstanz).
