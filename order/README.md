# Order files: exactly as sent to JLCPCB

`insect_tag_v8.3_jlc_order.zip` is the file uploaded for the first gantu-tag order on **6 November 2026**. It is
byte-for-byte the same file; check it with:

```
sha256sum -c SHA256SUMS
```

It holds one panel carrying both tags (Hagalu Gantu and Irulu Gantu):

| File in the zip | Upload it to |
|---|---|
| `insect_tag_v8_combined_panel_gerbers.zip` | JLCPCB → PCB (the Gerbers) |
| `insect_tag_v8_combined_panel_bom.csv` | PCB Assembly → BOM |
| `insect_tag_v8_combined_panel_pos.csv` | PCB Assembly → CPL (placement) |
| `README.md` | The ordering notes (the same as [`../panel/README.md`](../panel/README.md)) |
| `panel_top.png` | A picture of the panel, for checking |

The same Gerbers, BOM and CPL are regenerated from source in [`../panel/fab/jlcpcb_panel/`](../panel/fab/jlcpcb_panel/).

> **Status:** these tags are early pilots. The boards were ordered but not yet bench-tested when this was published.
> Check the latest notes in the [main README](../README.md) before you spend money.

## Order settings

### PCB

| Setting | Value |
|---|---|
| Layers / material | 2, FR-4 |
| Different Design in Panel | **2** |
| Delivery format | **Panel by Customer** (the frame, tooling holes and fiducials are already in the Gerbers) |
| PCB qty | 5 (the minimum) |
| **Thickness** | **0.6 mm** |
| Surface finish | ENIG recommended (LeadFree HASL also works at 0.6 mm) |
| Mark on PCB | Specify a location (the `JLCJLCJLCJLC` text on the bottom rail) |
| Via covering | Tented |
| Everything else | Default |

### PCB Assembly

| Setting | Value |
|---|---|
| Type | **Standard**: Economic only accepts 0.8–1.6 mm boards |
| Side | Top |
| **PCBA qty** | **2** panels, giving 36 tags (20 Hagalu and 16 Irulu) |
| Tooling holes | Added by customer |
| Confirm parts placement | Yes |

Rough cost on 6 Nov 2026 was **€250–280 before shipping and VAT, about €7 per assembled tag**. The parts are most of
that cost. Check stock in the cart: the IN100 (C6062024) and the TPS3831 (C2066667) were the tight ones.

### Placement preview: check these before paying

- **U1 (IN100):** the pin-1 dot sits next to the crystal.
- **Y1 (crystal):** a 90° rotation puts the crystal on GND and kills the tag; 180° is harmless.
- **U2 (TPS3831, Hagalu S tags only):** pin-1 dot at the upper left.
- **D2 (RB751, Hagalu S tags only):** cathode bar towards C5.
- **Photodiodes:** pad 1 is the cathode, marked by the silk bar. The middle row of each 2 × 3 block is turned 180°.

The bottom row of the panel is turned 180°, so its marks are too. Fix any offset in JLC's preview, not in the files.

## What comes back

| | Per panel | On 2 assembled panels |
|---|---|---|
| Hagalu S6 | 4 | 8 |
| Hagalu S6L | 4 | 8 |
| Hagalu N6 | 2 | 4 |
| Irulu V1 | 4 | 8 |
| Irulu V2 | 4 | 8 |

The 3 other panels come back bare (54 spare boards). The variant is printed on the underside of each tag.

Next: [programming](../docs/programming.md), then the finishing steps in [`../hagalu/README.md`](../hagalu/README.md)
and [`../irulu/README.md`](../irulu/README.md).
