# Pi bench

## Check BLE

The receiver runs on `walk-pi5` as `gantumoote-ble.service`. Open **Devices & connections → Flash history & Pi BLE** in Gantumoote to see the last local reception and download a 24-hour CSV. A Find My or Hubble location report in the map is a separate network observation.

Use the installed command in Terminal to list the Pi's known tags and stream selected tags:

```sh
gantu-ble -l
gantu-ble -d h03 h04
```

Each column shows the last packet time, RSSI, decoded temperature and raw BLE advertising bytes.
Use `--plain` for timestamped lines that you can save to a private log. Keep raw captures until you have used them.

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

## Hagalu-003 and Hagalu-004 solar bench (22 November 2026)

**Field candidate: Hagalu-004 (S6L, +4 dBm, programmed interval 6 s).** The programmed settings and
the programmer output hash are in [the flash record](tags.md#hagalu-004-find-my-field-candidate).

### Observed solar reception gaps

Both tags ran on solar for the 19:16–19:42 CET lamp ramp. The phone supplied illuminance readings.
The table reports gaps between adverts received by the Pi.

| Phone light | Hagalu-003 (0 dBm) | Hagalu-004 (+4 dBm) |
|---|---:|---:|
| ~23.6 klx | 2.07 s median | 2.11 s median |
| 12.2 klx | 4.34 s median | 5.32 s median |
| 6.0 klx | 11.08 s median | 14.43 s median |
| 3.0 klx | 30.58 s median | 37.77 s median |
| 1.59 klx | Two adverts, 125 s apart | Five adverts, gaps of 102–105 s |

At 12.2–3.0 klx, Hagalu-004 had 23–30% longer median gaps and a 6–7 dB median RSSI lead.
At 1.59 klx, it kept sending after Hagalu-003 was last heard. Both cadences changed as the lamp dimmed,
which fits recharge-limited operation. A VCC trace would establish whether each short gap includes a fresh startup.

### Window reception

The 19:50–20:05 CET run placed both tags outside with a window pane in the radio path to the Pi.
The tags cooled by about 8 °C. In the cold stretch the median RSSI was **−91 dBm for 003** and
**−87 dBm for 004**. Over the whole run the Pi heard **97 adverts from 003** and **237 from 004**.
Near the end, gaps clustered around multiples of about 2.45 s for 003 and 2.63 s for 004.
The phone supplied no new lux samples during the window run and was paused at the follow-up check.

The field decision is based on received adverts across the weak radio path. The dim-light bench intervals
show the corresponding cost in advert cadence where reception is already good.

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

## Program the next PCBA

1. Read the variant printed under the board. In Gantumoote’s Flash history, select the next unburned tag and download its own config and key.
2. Follow [the programmer steps](programming.md#steps). After a successful OTP write, save the tool’s emitted `nano_beacon_config.cfg` and the matching packet and raw dumps before running the tool again. On the Mac they appear in `~/Library/Logs/nanobeacon/`.
3. Archive the exact tool output on the Pi using [Gantumoote’s flash command and sealing steps](https://github.com/pvnkmrksk/gantumoote#flash-history-and-pi-ble). Check the displayed record, compare its SHA-256 to the local file and confirm a local BLE reception after power-cycling. Record the board, network and hash in [the tag register](tags.md).
