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

### The Hagalu catch

A RAM configuration lasts only while the adapter powers the tag. Unplug it and the capacitor drains, so the
configuration is gone. To test Hagalu in light, **burn the OTP on one tag**, then compare the variants
(S6, S6L, N6) before burning many.

## Network payloads

- **Find My** (OpenHaystack static key, the default for the first units): non-connectable advertising with the payload
  `1E FF 4C 00 12 19 00 <key bytes 6–27> <key[0] >> 6> 00` and the static random address `key[0] | 0xC0, key[1..5]`.
  Check the bytes in nRF Connect against an ESP32 running the same key.
- **Hubble:** follow Hubble's IN100 guide. No hardware change is needed.

Hagalu keeps no clock in the dark. That's fine for Find My; for Hubble the time counter restarts every morning.
