# Programming a gantu tag

Both tags carry an InPlay **IN100 NanoBeacon**. It runs no firmware you write: everything it transmits (address,
advert data, interval, TX power) is a configuration loaded over its UART. You can test a configuration in RAM as
often as you like, but writing it to the chip's one-time-programmable memory (**OTP**) can be done **only once**.

**A blank tag does not advertise.** Nothing shows up in a BLE scanner until you've loaded a configuration.

## What you need

- **A 3.3 V USB-to-serial adapter** (USB-UART or USB-TTL), such as a CP2102, CP2104, CH340 or FTDI board set to
  3.3 V. A plain USB cable is not enough. **Never use 5 V logic**: the IN100's absolute maximum is 3.6 V.
  - Its 3.3 V output must supply **at least 100 mA**: burning the OTP needs up to 50 mA, and on Hagalu the dark
    photodiodes draw up to about 7 mA more. An FT232R's built-in 3V3OUT is too weak; a board with its own 3.3 V
    regulator is fine.
  - A Raspberry Pi's UART also works (pins 1, 6, 8 and 10 below), but InPlay's tool then has to run on the Pi.
- **InPlay's NanoBeacon Config Tool** (Windows, macOS, Linux), from inplay-tech.com.
- **4 wires** to the tail. The tail has four plated holes, **Ø 1.6 mm in a 2 × 2 grid at 2.54 mm pitch**, so a
  standard 2.54 mm header, a 2 × 2 Dupont housing or a pogo jig fits directly.
- A phone with a BLE scanner, such as nRF Connect.

## Wiring

| Tail pad | Adapter | Raspberry Pi (physical pin) |
|---|---|---|
| **+** (VCC) | 3.3 V | 1 (3.3 V) |
| **G** (GND) | GND | 6 (GND) |
| **R** (RXD, into the IN100) | TX | 8 (GPIO14, TXD) |
| **T** (TXD, out of the IN100) | RX | 10 (GPIO15, RXD) |

- **Connect + and G before R and T**, or put 1–4.7 kΩ in series with the adapter's TX. A powered UART line into an
  unpowered IN100 can back-power it and leave it in an undefined state.
- If the tool doesn't find the chip, swap R and T: that's the usual mistake.
- **Irulu: never connect the programmer once a cell is fitted.** It would drive 3.3 V into the cell.
- **Hagalu: program in dim light.**
- On a Pi, never use pins 2 or 4 (5 V). Turn on the UART with `sudo raspi-config` → Interface Options → Serial
  (login shell **No**, serial hardware **Yes**), reboot, and use `/dev/serial0`.

## Steps

1. **Run in RAM first.** Load a simple advert (iBeacon, Eddystone or custom manufacturer data, with a name you'll
   recognise) and check it in nRF Connect. This proves the IN100, the crystal and the radio work. No antenna wire is
   needed at desk range.
2. **Settings for the first units:** 0 dBm, 1 Mbps PHY, **3 s or longer** interval. Set the XO load capacitance to
   about 6–6.5 pF. On Irulu with a 337 cell, stay at 0 dBm; use +4 dBm only with a 364/377 cell.
3. **Burn the OTP** only once the RAM test works. Then remove power and reconnect it: the tag now runs on its own.

**One RAM load per power-up.** Once a configuration is running, the IN100 stops answering the tool. Connect fails
with "Failed to connect to an IN100 dev board", and Run in RAM either fails ("Failed to connect to the device") or
reports Done without changing anything. To load another configuration, load the file in the tool first, then unplug
the adapter, plug it back in, click Probe and Connect straight away, and Run in RAM once. A Connect a minute after
power-up sometimes failed on the bench; one made straight away worked every time.

### The Hagalu catch

A RAM configuration lasts only while the adapter powers the tag. Unplug it and the capacitor drains, so the
configuration is gone. To test Hagalu in light, **burn the OTP on one tag**, then compare the variants
(S6, S6L, N6) before burning many.

## Network payloads

- **Find My** (OpenHaystack static key, the default for the first units): non-connectable advertising with the payload
  `1E FF 4C 00 12 19 00 <key bytes 6–27> <key[0] >> 6> 00` and the static random address `key[0] | 0xC0, key[1..5]`.
  Check the bytes in nRF Connect against an ESP32 running the same key.
  - **Entering it in the Config Tool** (checked on a Hagalu S6 on 19 Nov 2026): edit Advertising set #1 → Custom →
    tick only **Manufacturer Specific Data**. Set **ID** to `0x004C` and put the remaining 27 bytes in **Data**
    (`12 19 00 <key 6–27> <hint> 00`, typed as hex without spaces). Leave Extended Data empty. The tool adds the
    `1E FF` header itself and no flags field, so the advert is exactly 31 bytes.
  - **The tool takes the address byte-reversed.** To make scanners show `F6:AF:67:80:2E:FD`, type
    `FD:2E:80:67:AF:F6`. Check it on a scanner that shows addresses (iOS hides them; the NanoBeacon scanner app
    showed it).
- **Hubble** (checked on Hagalu-002 on 20 Nov 2026: decoded locally and seen in the Hubble app). No hardware change
  is needed.
  1. **Register the device with Hubble:** encryption **AES-128-EAX**, counter mode **DEVICE_UPTIME**, period exponent
     **15**. Hubble gives you the device's AES-128 key. The key, the period exponent and the counter mode must match
     the tag exactly: Hubble drops mismatched packets without saying so.
  2. **Make the configuration.** Download one of Hubble's sample configs from
     [hubble-inplay-cfg/samples](https://github.com/HubbleNetwork/hubble-inplay-cfg/tree/main/samples) (any
     interval; it isn't copied here because that repository has no licence), then run
     `python3 new_hubble_tag.py hagalu_002 hubble-in100-4s-advinterval.cfg` and paste the key when asked. It
     writes `hagalu_002.hubble.cfg` and `.key` to `~/Documents/KiCad/gantu_keys/` (keep both private), with a 4 s
     interval, 0 dBm, XO cap code 8 and the sensor payload below.
  3. **Load it:** in the Config Tool, Load the `.cfg`, power-cycle the tag, Probe and Connect straight away, then
     Run in RAM (see "One RAM load per power-up"). Leave the advertising data format on **Custom**.
  4. **Check it:** copy the service data of UUID `0xFCA6` from nRF Connect and run
     `python3 hubble_decode.py ~/Documents/KiCad/gantu_keys/hagalu_002.hubble.key <hex>`. It checks the rotating
     ID against the key, verifies the auth tag and prints the sensor values. Then open the Hubble app near the tag.
  - **Don't use the Config Tool's own "Hubble" data format** (V3.0). It sends the payload unencrypted and marks no
    field as the last encrypted one (the tool's own packet dump shows this), so the tag can't build the AES-EAX
    tag: nothing decoded on the bench. Hubble's template marks the payload as encrypted
    (`<EncRaw FF 1byte 0 1>`), and the script keeps that.
  - **Sensor payload** (`--payload sensors`, the default): 7 encrypted bytes, little-endian. `--payload ff` sends
    Hubble's 1-byte default instead.

    | Bytes | Field | Config Tool token | Value |
    |---|---|---|---|
    | 0 | VCC | `<VCC 1byte 0 1>` | × 0.03125 V |
    | 1–2 | IN100 temperature | `<TEMP 2byte 0 1>` | signed, × 0.01 °C |
    | 3–6 | Advertising count | `<ADVCNT 4byte 0 1>` | adverts since power-up |

    For example, `6d cc07 0f000000` is 3.406 V, 19.96 °C, advert 15 (on the adapter's 3.3 V supply). Hubble's
    packets API and webhooks return this payload already decrypted, as base64; `parse_sensors()` in
    `hubble_decode.py` turns it into values. The advert is now 30 of the 31 bytes, so there's room for one more
    byte; a 2-byte count (≈ 3 days at 4 s) would free two.

Hagalu keeps no clock in the dark. That's fine for Find My. For Hubble, the uptime counter and the advertising count
restart every morning. Hubble's reference decoder (pyhubblenetwork) tries the first 128 rotation periods from zero
(≈ 48 days at exponent 15), so a restarted tag still decodes: on the bench it decoded after every power cycle, and
the Hubble app showed it.
