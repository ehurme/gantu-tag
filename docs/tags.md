# Tags

What each programmed tag carries, so a burned tag can be traced back to its configuration. Keys and full `.cfg`
files hold secrets: they stay in `~/Documents/KiCad/gantu_keys/` (keep a backup) and never go into this repo. The
hash identifies the exact file.

## Hagalu-002 (Hubble)

| | |
|---|---|
| Board | Hagalu v8.3, the second bench tag |
| Network | Hubble, device "Hagalu-002": AES-128-EAX, counter mode DEVICE_UPTIME, period exponent 15 |
| Made with | `new_hubble_tag.py hagalu_002 hubble-in100-4s-advinterval.cfg --payload sensors` ([how](programming.md#network-payloads)) |
| Advert | every 4 s, 0 dBm, 1 Mbps, channels 37–39, private non-resolvable address renewed every 90 s, XO cap code 8 |
| Payload | encrypted, little-endian: VCC (1 byte, × 0.03125 V), IN100 temperature (2, × 0.01 °C), advert count (4) |
| Private files | `hagalu_002.hubble.key`; `hagalu_002.hubble-sensors.verified-2026-11-20.cfg` (+ `.packet.txt`, `.raw.txt`) |
| Config sha256 | `80c55e3b119e77e2c8e7de9a3a8e5b557cfa24399417cad0933356bd14b170c0` |
| Verified | 20 Nov 2026, from RAM on the adapter: decoded locally (3.406 V, 19.9–20.3 °C, count rising by one per advert) and seen in the Hubble app. A dry run just before burning sent a byte-identical config and image. |
| OTP | burned 20 Nov 2026, 16:44. The tool's record of what it sent is byte-identical to the verified config. |
