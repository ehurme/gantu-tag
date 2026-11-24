# Pi bench

## Check BLE

The receiver runs on `walk-pi5` as `gantumoote-ble.service`. Open **Devices & connections → Flash history & Pi BLE** in Gantumoote to see the last local reception and download a 24-hour CSV. A Find My or Hubble location report in the map is a separate network observation.

Use the installed command in Terminal to list the Pi's known tags and stream selected tags:

```sh
gantu-ble -l
gantu-ble -d h03 h04 h05 h06 --record
```

Each column shows the last packet time, RSSI, decoded temperature and raw BLE advertising bytes.
`--record` puts a private TSV and PNG beside each other in `~/blelog` on the Pi. Use the same command with
`--plain` in a background job. On the Mac, run `gantu-ble --plot latest` to open the newest recording in your image
viewer. The launcher saves the PNG in `~/Downloads/Gantu BLE`. Pass the exact TSV path instead of `latest` to open
an older run. See [the Gantumoote recorder instructions](https://github.com/pvnkmrksk/gantumoote#flash-history-and-pi-ble)
for installation and light logging.

For a day-long trace, use the boot-enabled `gantumoote-ble-recording.service`. It records keyed tags to
a fresh private TSV every 24 hours while Bluetooth discovery keeps running. The monitor and recorder
restart if the scan loop stalls. To review a day remotely, sign in to Gantumoote and open
**Flash history & Pi BLE → View daily BLE and Find My plots**. Pick a date and enter tag names if needed.
The same plot is available from the terminal:

```sh
gantu-ble --plot-day 2026-11-23 --tags h03 h04 h05 h06
```

The minute history covers the whole day. The reception-gap panel uses detailed TSVs wherever they exist.
Faint guides mark Find My observation times. Hover, tap, or choose a report to inspect nearby adverts.
Rings mark one plausible Pi advert and crosses mark several. Use **Advert matches CSV** below the plot
to compare the Find My observation and Pi packet timestamps. Expand **Diagnostics** for Pi
heartbeats, older service intervals, and Find My poll activity on the same time axis.

From the Pi checkout:

```sh
cd ~/gantumoote
systemctl status gantumoote-ble --no-pager
sudo journalctl -u gantumoote-ble -n 25 --no-pager
ls -lh ~/blelog
/usr/bin/python3 -m dashboard.ble capture ~/blelog/burn.btsnoop
```

The `burn.btsnoop` capture spans 12:09–12:29 CET on 22 Nov 2026. A second capture covers 16:42:27–16:42:47 CET, before Hagalu-003’s recorded OTP output. The 17:08–17:09 CET capture contains nine matching Hagalu-003 Find My adverts. The filename and modification time alone do not establish the capture window.

The separate overnight file `night.btsnoop` ran from 23:23:19 CET on 21 Nov to 12:08:09 CET on 22 Nov. The
original analysis recorded Hagalu-006 on USB adapter power at 3.406 V. The Pi heard 4,409 Find My adverts,
2,525 authenticated Hubble adverts and one zero-key Hubble advert at startup. The raw copies were deleted
after that analysis. The dashboard preserves the totals. That run does not establish an OTP burn or a solar start.

Every 22 Nov bench recording from `~/blelog` (the `h03-h04-*` and `h05-*` TSVs with their `.lux.tsv` files, plus
`post-burn-interval-IxdYlR.btsnoop` and `monitor-diagnostic.btsnoop`) is also copied, read-only, into
`dashboard/data/secrets/ble-captures/`, which the daily backup includes. The runs cited below are listed under
**Saved BLE captures** in Flash history.

## Hagalu-003 and Hagalu-004 solar bench (22 November 2026)

**Field candidate: Hagalu-004 (S6L, +4 dBm, programmed interval 6 s).** The programmed settings and
the programmer output hash are in [the flash record](tags.md#hagalu-004-find-my-field-candidate).

### Observed solar reception gaps

Both tags ran on solar for the 19:16–19:42 CET lamp ramp. The phone supplied illuminance readings.
The table reports gaps between adverts received by the Pi.

| Phone light | Hagalu-003 (0 dBm) | Hagalu-004 (+4 dBm) |
|---|---:|---:|
| ~23.6 klx (read at 19:01, before the run) | 2.07 s median | 2.11 s median |
| 12.2 klx | 4.34 s median | 5.32 s median |
| 6.0 klx | 11.08 s median | 14.43 s median |
| 3.0 klx | 30.58 s median | 37.77 s median |
| 1.59 klx | Two adverts, 125 s apart | Five adverts, gaps of 102–105 s |

At 12.2–3.0 klx, Hagalu-004 had 23–30% longer median gaps and a 6–7 dB median RSSI lead. Both cadences
changed as the lamp dimmed, which fits recharge-limited operation.

At the brightest step both tags sent about every 2.1 s. That is faster than either programmed interval (3 s and
6 s) and almost the same at 0 and +4 dBm. So each advert there came from a fresh start, and neither tag stayed on.
The roadmap expected the IN100 to stay on in bright light. It didn't at the ramp's brightest step.

At 1.59 klx, Hagalu-004 kept sending after Hagalu-003 was last heard at 19:37:23. Recharge alone predicts the
opposite, because 003 spends less charge per advert. Two explanations fit:

- **003 sat in dimmer light under the lamp.** Swap the two tags and repeat the dim step.
- **003 spent extra charge after some starts.** On S6L, CHIP_EN is held for about 3.3 s. That is longer than
  003's 3 s interval, so a second advert can fire before the chip turns off. 004's 6 s interval rules that out.
  The ramp shows no pairs of adverts 3 s apart, so there is no direct sign of this. A VCC trace on the tail would
  settle it.

The S6L lock test is still open. It needs a slow rise from dark (a dawn ramp) with VCC on the scope, and this
ramp went from bright to dim.

### Window reception

The 19:50–20:05 CET run placed both tags outside with a window pane in the radio path to the Pi.
The tags cooled by about 8 °C. In the cold stretch the median RSSI was **−91 dBm for 003** and
**−87 dBm for 004**. Over the whole run the Pi heard **97 adverts from 003** and **237 from 004**.
Near the end, gaps clustered around multiples of about 2.45 s for 003 and 2.63 s for 004.
The phone supplied no new lux samples during the window run and was paused at the follow-up check.

The field decision is based on received adverts across the weak radio path. The dim-light bench intervals
show the corresponding cost in advert cadence where reception is already good.

The comparison rests on one tag of each. Across the window, 004's lead was 4 dB, the same as the power
difference. On the bench it was 6–7 dB, so placement or antenna added to it there. Swapping the two tags' places
would separate the tag from its setting.

### Two regimes in one run

The 20:22–20:38 CET recording shows both ways a tag can run:

- **Restarting for each advert.** With the phone at about 4.9 klx, Hagalu-004's gaps were 17.7 s (or twice that,
  after a missed advert) and Hagalu-003's about 13.7 s. That is the same ratio as in the ramp. The tags followed
  the light, not their settings.
- **Staying on.** From 20:36:34 to the end, Hagalu-003 sent every 3.0 s and Hagalu-004 every 6.0 s, exactly
  their burned intervals. This confirms on air that 004 carries its 6 s setting. The phone read 230–250 lx then,
  and the tags warmed from 14.5 to 19 °C, so the phone's reading no longer described the tags' light. What
  changed isn't recorded. If the tags were still on solar, this is the first time a Hagalu tag was seen staying on.
  The 22:05 same-lamp test below shows the same steady 3 s cadence from Hagalu-003 and -006.

## Hagalu-005 N6 startup check

On 22 Nov 2026, the one-wire RAM run yielded 18 matching adverts over 57 s. Fifteen gaps were
2.94–3.05 s and two were near 6 s. The median RSSI was −45 dBm. The operator then confirmed the OTP
burn. The programmer output and its settings are in [the flash record](tags.md#hagalu-005-find-my-n6-startup-pilot).

The Pi last heard Hagalu-005 at 21:12:07 CET. A recording begun at 21:14 CET heard zero adverts
during the subsequent solar attempt. Confirm a fresh OTP boot on regulated 3.3 V and GND alone,
then test from fully dark under bright, even light while scoping VCC across the tail's + and G pads.
That checks whether the N6 wakes before the capacitor holds enough charge for the first burst.

The operator subsequently reported radio silence on the DC boot check and set the pilot aside.
The failed DC boot leaves the solar-start mechanism unconfirmed.

The Pi also heard seven adverts after a gap that fits the burn: nothing from 21:11:30 to 21:11:49.9, then adverts
every 3 s until 21:12:07. The first came in the same second the programmer saved its output. If the Config Tool
restarts the chip from OTP after burning, the burned image ran, and what failed is the N6 starting on its own. If
those adverts came from the tool's RAM copy, the OTP contents are still unproven. The planned pre-burn CHIP_EN
check (a 10 MΩ meter at C5 on the adapter) wasn't recorded.

To tell these apart, power Hagalu-005 from regulated 3.3 V and read CHIP_EN at C5 and the supply current:

- **CHIP_EN near VCC but no adverts:** the chip is enabled, so the burned image (or the chip) is at fault.
- **CHIP_EN well below VCC:** something loads it, which is what the pre-burn check was for, and a 1 MΩ enable
  won't do. Irulu V2's 100 kΩ enable is the hedge.

Also try connecting with the programmer. Whether the chip still answers shows whether it is alive. Until this is
known, the other N6 boards stay unburned.

## Hagalu-006 and Hagalu-003 same-lamp test

Both tags used Find My at **0 dBm / 3 s**. Over the 269 s common window of the 22:05:59–22:10:36 CET
recording on 22 Nov 2026, under the same lamp, the receiver logged:

| Tag | Hardware | Adverts received | Median reception gap | Median RSSI |
|---|---|---:|---:|---:|
| Hagalu-003 | S6L | 73 | 3.002 s | −59 dBm |
| Hagalu-006 | S6 | 75 | 2.995 s | −60 dBm |

Both had stable clusters around 3 s, with longer gaps mainly near multiples of 3 s.
The run establishes a same-lamp baseline. A matched dim-light ramp and cold starts are the tests
for the different enable hold times. [Hagalu-006 flash record](tags.md#hagalu-006-find-my-s6-comparison-pilot).

## Program the next PCBA

1. Read the variant printed under the board. In Gantumoote’s Flash history, select the next unburned tag and download its own config and key.
2. Follow [the programmer steps](programming.md#steps). After a successful OTP write, save the tool’s emitted `nano_beacon_config.cfg` and the matching packet and raw dumps before running the tool again. On the Mac they appear in `~/Library/Logs/nanobeacon/`.
3. Archive the exact tool output on the Pi using [Gantumoote’s flash command and sealing steps](https://github.com/pvnkmrksk/gantumoote#flash-history-and-pi-ble). Check the displayed record, compare its SHA-256 to the local file and confirm a local BLE reception after power-cycling. Record the board, network and hash in [the tag register](tags.md).
