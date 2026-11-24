# IN100 Config Tool and CFG reference

The macOS IN100 Config Tool **4.0.0 (2026-10-30)** exports JSON with CFG `version: "3.17"`. I changed Advanced controls, saved and reloaded the exports, and ran synthetic configs through the installed RAM configuration compiler. The [payload reference](in100-manual.md) covers byte selection, scaling, and the fields found beyond InPlay's guide. The remaining verification is on the radio.

## Advanced Settings to CFG

Open **Application Settings → Advanced → Enter Advanced Mode**. Use **Add** to append a command, **Insert** to put it before the selected row, and **Delete** to remove a row. Click **OK**, then **Save**. To make the same changes directly, update these top-level fields in a copy of the CFG and use **Load**.

| UI control | JSON field | Values and effect |
| --- | --- | --- |
| Special Register Settings | `regSettingCust` | Ordered array of command strings. Comments survive Save and Load. |
| GUI RunTime Settings | `guiRuntimeCfg` | String of semicolon-delimited assignments. For example, `"tx_interval_max=45000;"` sets the desktop validation ceiling in milliseconds. Use `advSet[].interval` to change the requested interval. |
| Register value trigger enable | `regValTrigEn` | `0` or `1`. Reaches the Region 1 register-value-trigger flag. Global Trigger Settings continues to show the same sensor inputs with the flag enabled. |
| Key 1 and 2 not used | `r2Overlay` | `3`. Reuses those key slots in the eFuse layout. Key 0 remains available. |
| All keys not used | `r2Overlay` | `7`. Reuses all three slots. Save rejects configurations that need the disabled keys. With both overlay controls off, the export omits the field and the loader uses `0`. |
| Compact size for eFuse region 2 | `settingPolice` | `1` for storage first, `0` for power first. Changes the layout policy used to compile the configuration. |

`regSetting` is the tool-managed list of default register writes. The compiler reads an imported list, and a GUI save can regenerate it. Put custom commands in `regSettingCust` to preserve them across a GUI round trip. `custRegPattern.hubbleRotation127reset` is a separate Hubble-specific setting that can generate writes and enable register-value triggering.

`guiRuntimeCfg` also recognizes `gpio_limit` and `dfn8_limit` in the DFN8 pin checks, and `hubble_limit` in the tool's Hubble validation. The app contains a parser for `rpa_limit` with no call site found in this build. These keys affect the desktop tool's behavior. Evidence comes from `AdvancedSettingWidget` and the main window's configuration validation.

### Register commands

| Command in `regSettingCust` | Arguments |
| --- | --- |
| `write: BOOT EVENT SIZE ADDRESS VALUE` | Write a constant. `SIZE` is `0`, `1`, `2`, or `3` for one through four bytes. |
| `read-modify-write: BOOT EVENT SIZE ADDRESS VALUE MASK` | Masked constant update to the addressed register. Supply a nonzero mask and place the replacement bits at their target positions. |
| `delay: BOOT EVENT MICROSECONDS` | Delay for the specified interval. `20` means 32 µs. Positive delays through `ffffff` pass the GUI parser. |

Use hexadecimal arguments separated by spaces. The vendor examples use boot code `0` for cold, `1` for warm and `3` for either. Event `1` is wakeup. InPlay's trigger table includes peripheral-completion events and a before-sleep event. These events schedule commands within a wake cycle. Advertising triggers use a separate set of controls. [InPlay cached-data note, tables 1–3](https://github.com/NanoBeacon/config-files/tree/main/Store%20Cached%20Data#register-write-and-delay-commands).

Suffix a command with `@h` to place it before generated/default writes. Ordinary commands follow the generated writes, with the original relative order retained within each group. A generated write later in the same event can overwrite an `@h` write. The UI accepts a leading `register ` and strips it before saving. In a hand-written CFG use the forms above, since the compiler supplies that prefix. Lines beginning with `#` and trailing `#` comments survive Save and Load.

The stock parser recognizes the three commands above. The editor rejected a `shift:` probe, and the packet compiler has no general-purpose shift or arithmetic opcode. InPlay's word-copy engine can copy source registers into SRAM and shift the position of whole samples through a history buffer. To narrow a live value by eight bits, select its upper byte. ADC unit mapping gives finer control over the scale. [InPlay Config Tool User Guide, Advanced Settings](https://www.manualslib.com/manual/3441367/Inplay-Nanobeacon-In100.html?page=47), [InPlay cached-data note](https://github.com/NanoBeacon/config-files/tree/main/Store%20Cached%20Data#implementing-cached-data-feature).

### Other settings by CFG section

| UI or tool feature | CFG location and behavior |
| --- | --- |
| Advertising Data and Encryption | `advSet[].ui_format`, `payload[]`, `authEn`, `authKey`, `rot_exp`, `authSaltType`, `authSaltValue`, `authEaxCountType`, `authEaxCountValue`. Payload entries store an AD type, a length and hex or dynamic tokens. |
| Advertising Parameters and Advanced Advertising | `advSet[].interval`, `phyRate`, `chCtrl`, `randomDlyType`, `bdAddr`, `addrType`, `addrKey`, `staticAddrGen`, `addrGenInterval`, `cte` and `cteLen`. Advanced framing uses `isStandardBle`, `accessCode`, `header` and `headerMsb`. The loader accepts `addrType: "notPresent"` for custom framing. |
| Triggered advertising | `advSet[].advModeTrigEn` and per-set mode settings. The global sensor map uses `triggerEn`, `trig1Src` through `trig4Src`, `trig1Low` through `trig4Low`, and `trig2High` through `trig4High`. The UI offers VCC, temperature, ADC, 1-Wire and I²C inputs with choices depending on the slot. |
| ADC and measurement units | `adc[]` holds channel enable, pin power controls, skipped and averaged samples, and the unit mapping. Top-level `vccUnit` and `tempUnit` scale the on-chip sensors. `calibration` carries calibration inputs. |
| I²C slaves | `i2c`, `i2c2`, `i2c3` hold boot controls, power/pin/bus settings, read-data storage and the command sequence. The UI loader uses `memStoreLen`, `memStoreOffset` and `cmd`. The payload offset selects from that stored data. |
| GPIO, edge count, pulse and square wave | `gpio[]`, `edgeCount`, `pulse` and `sqWave`. Includes pin mode, pull, sleep latch, wakeup, advertising triggers, edge-count source, 1-Wire pulse timing and square-wave start/clear controls. |
| XO, Transmit, Keys and Product ID | `txSetting` holds `xoCap`, `xoStableTime`, `xoGm`, `txPower`, `txPaGain`, `sleepAftTx`, `custUUID` and optional `key0` through `key2`. |
| Watchdog and 32K RTC | `wdt` and `rtc`. The CFG stores watchdog enable, wake behavior and initial value, and RTC enable and clock selection. |
| RF Test and Advanced Debug | Live UART tools for RF test modes and register, memory or eFuse access. Their controls are outside the stored advertising CFG. |

The regular panels are covered in the InPlay guide. The vendor sample repository includes working I²C sensor and advertising configurations. [InPlay Config Tool User Guide](https://www.manualslib.com/manual/3441367/Inplay-Nanobeacon-In100.html), [InPlay vendor samples](https://github.com/NanoBeacon/config-files).

### Compare an additional control

Start with a key-free config. Save a baseline, change one control, confirm the editor with **OK**, and save to a second path. Compare the JSON and try the same change in a copy of the baseline. Reload and save it again to see what the tool normalizes. Keep these CFGs and any diffs containing private values in the ignored local key folder.

```sh
python3 -m json.tool --sort-keys before.cfg before.json
python3 -m json.tool --sort-keys after.cfg after.json
diff -u before.json after.json
```

## Reproduce the high-byte check

For a little-endian 16-bit SRAM value at `0x2F80`, `<REG2f81 1byte 0 0>` reads its high byte. For example, this Manufacturer Specific Data entry emits one dynamic byte after the two-byte company ID. Its `len` includes the AD type byte.

```json
{"len": 4, "type": 255, "data": "ffff<REG2f81 1byte 0 0>"}
```

In the UI, use **Advertising → Edit → Advertising Data → Custom → Settings → Manufacturer Specific Data → EDIT**. Register Read Data is in the Extended Data picker. The data text box also accepts the token directly. The GUI export, Load operation and raw preview preserved the explicit odd address. The preview mislabeled the flags on a one-byte field with a nonzero endian flag, so the [payload reference](in100-manual.md#transmitting-the-high-byte) uses the compiler's descriptors to report flag behavior.

Generate a key-free test CFG with [`tools/in100_msb_probe.py`](../tools/in100_msb_probe.py).

```sh
python3 tools/in100_msb_probe.py /tmp/in100-msb-1234.cfg
python3 tools/in100_msb_probe.py /tmp/in100-msb-00ff.cfg --value 0x00ff
python3 tools/in100_msb_probe.py /tmp/in100-msb-0100.cfg --value 0x0100
python3 tools/in100_msb_probe.py /tmp/in100-msb-ffff.cfg --value 0xffff
```

The CFG writes an aligned test word to the vendor's SRAM cache area on wakeup. It advertises the same word as two bytes in each byte order, then reads the base and upper byte addresses individually. The command prints the expected AD structure, including AD length and type. For `0x1234` the expected bytes are `0a ff ff ff 5a 34 12 12 34 34 12`. Across the `0x00FF` to `0x0100` boundary, the standalone low byte goes from `ff` to `00`, while the high byte goes from `00` to `01`. The GUI loaded and re-exported the probe, and the installed RAM compiler packed all four variants.

On a connected bench tag, load one file and choose **Run in RAM**. Check the raw advertising bytes using the [Pi bench runbook](pi-bench.md). Power-cycle before loading another variant. Once the SRAM byte read is established, compare a direct internal ADC or temperature register read with a word copied to SRAM.

## Stagger Find My and Hubble adverts

The IN100 can run both networks from one tag on **independent intervals**. Each configured set has its own address, payload, interval and channel selection. TX power and other radio settings, GPIO configuration, and measurement units are shared.

Use the existing [combiner](../tools/combine_cfg.py) with two single-set CFGs. This example uses Find My at 3 s and Hubble at 10 s. Set the Hubble interval when generating its input so the rotation timer is recalculated. Run these commands from the repo root and keep the keyed files in the private directory.

```sh
keys_dir="${GANTU_KEYS:-$HOME/gantu-keys}"
python3 tools/new_hubble_tag.py my_tag --interval 10 --out-dir "$keys_dir"
python3 tools/combine_cfg.py "$keys_dir/my_tag.findmy.cfg" "$keys_dir/my_tag.hubble.cfg" \
  --interval1 3 -o "$keys_dir/my_tag.dual.cfg"
```

On Hagalu-006 in RAM on 21 November 2026, both networks received this 3 s / 10 s setup. While the chip stayed powered, jitter let the two schedules slide past each other. The closest recorded pair after startup was 13.5 ms apart in the 150 s capture. On power-up both sets advertised within 1.6–2.5 ms of one another in the recorded trials. Reversing set order still produced back-to-back startup adverts. The CFG exposes per-set intervals and random delay, with no verified fixed phase or cold-start offset. A larger `randomDlyType` is jitter. Triggered advertising can wait for an external event. The Advanced `delay:` command delays a scheduled register sequence and has no per-set selector.

Hagalu's solar design can cold-start for each advert in dim light, so two intervals alone cannot spread the startup load. For a dual-network bench trial, measure the supply through startup and try the combiner's per-set channel options if charge is tight. The RAM trials also emitted a zero-key first Hubble packet with Hubble alone and in either set order. A burned Hubble-only tag has sent a valid first packet. Dual-set OTP startup remains unverified. [Bench notes in the combiner](../tools/combine_cfg.py), [InPlay Config Tool User Guide, advertising parameters](https://www.manualslib.com/manual/3441367/Inplay-Nanobeacon-In100.html).

## Count activity with a ball switch

**GPIO Edge Count** counts rising transitions on a configured input, including in deep sleep. The hardware count is 24-bit. The payload width just controls how many bytes are sent. InPlay specifies high and low periods longer than 1 ms. Give the input a defined pull, and check contact bounce if one mechanical movement should count as one event. The example uses GPIO2 with a pull-down so a switch closure to VDD makes the rising edge. On the v8.3 Hagalu and Irulu boards, GPIO2 is unconnected at U1 pad 10 and is absent from the programming tail. [InPlay Config Tool User Guide, §2.3](https://dfimg.dfrobot.com/nobody/wiki/5d9b79a87f78ef9c0fe3c98077f89809.pdf#page=36), [Hagalu PCB](../hagalu/insect_tag_v8_solar.kicad_pcb), [Irulu PCB](../irulu/insect_tag_v8_battery.kicad_pcb).

Set GPIO2 to input in `gpio[]` with `"digital": "ie"`, `"pu-pd": 2` and `"latch": 1`. Then enable the edge counter and leave the automatic clear flags off for accumulation across adverts and sleep.

```json
"edgeCount": {
  "enable": 1,
  "srcPin": 2,
  "countEdge": 1,
  "clearByTx": 0,
  "clearBySleep": 0,
  "clearByEvent": 0
}
```

| Payload token | Compiler descriptor | What the compiler requests |
| --- | --- | --- |
| `<EDGE 3byte 0 0>` | `1d 03` | Full GPIO count in little-endian order |
| `<EDGE 3byte 1 0>` | `3d 03` | Full GPIO count in big-endian order |
| `<EDGE 1byte 0 0>` | `1d 01` | One byte with the little-endian flag |
| `<EDGE 1byte 1 0>` | `3d 01` | One byte with the big-endian flag |

The `EDGE` descriptors expose no source address or byte offset. The one-byte variants leave the descriptor's MSB/LSB selector at zero. The big-endian variant still needs a BLE check to determine which byte the chip emits. The compiler's writes to `0x32EC` and `0x0B40` configure the feature and do not establish the address of the live count. If InPlay supplies the address, test a one-byte read at the base plus two for a little-endian count. The vendor's register copy engine offers a fallback through SRAM if an unaligned direct read fails. [InPlay cached-data note](https://github.com/NanoBeacon/config-files/tree/main/Store%20Cached%20Data).

The top byte is `count >> 16`. It stays at zero for 65,535 edges and first changes at edge 65,536. It spans the full 24-bit range in coarse steps, and the count loses continuity when Hagalu loses power. If the receiver sees a verified low-byte field on the same boot with fewer than 256 edges between observations, it can recover the increment as `(new_byte - old_byte) & 0xff`. Use the full count when those assumptions are too restrictive.

### Fit the full activity count into Hubble

Keep the Find My payload unchanged. In the repo's Hubble sensor payload, shorten the diagnostic advertising count from four bytes to two and append the encrypted three-byte switch count just before the authentication tag. This keeps VCC and temperature and makes a **31-byte advert**. Change the raw service-data AD length from `19` to `1a` and the enclosing payload `len` from `30` to `31`.

```json
{"len": 31, "type": 254, "data": "0303a6fc1a16a6fc08<SALT 2byte 0 0><EID 8byte 1 0><VCC 1byte 0 1><TEMP 2byte 0 1><ADVCNT 2byte 0 1><EDGE 3byte 0 1><TAG 4byte 0 0>"}
```

Apply the change to the Hubble set in the combined CFG and enable the GPIO counter globally as above. The eight decrypted bytes are VCC (1), temperature (2), advertising count (2), and switch count (3), all little-endian. The existing `hubble_decode.py` prints the authenticated plaintext hex for this layout. Its automatic sensor formatting expects the original seven-byte layout. The shorter reporting field leaves the separate Hubble EID rotation settings intact.

### Verify the one-byte field on the bench

```sh
python3 tools/in100_msb_probe.py /tmp/in100-gpio-edge.cfg --gpio-edge
```

Load the key-free fixture in RAM on a bench board with GPIO2 available. Feed a shared-ground square wave from 0 to the chip supply voltage. At 400 Hz with 50% duty, both levels last 1.25 ms and 65,536 edges take about 164 seconds. Keep the chip powered throughout and capture its adverts locally. After manufacturer data marker `5b`, compare the three-byte little-endian reference with the two one-byte fields. Near `0x00FFFF → 0x010000`, the high byte rises from `00` to `01`; the low byte rolls from `ff` to `00`. The current evidence is from the compiler. This capture would establish the hardware behavior.
