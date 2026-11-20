# Tags

What each programmed tag carries, so a burned tag can be traced back to its configuration. Keys and full `.cfg`
files hold secrets: they stay in the private key folder (`$GANTU_KEYS`; keep a backup) and never go into this repo.
The hash identifies the exact file.

## Hagalu-002 (Hubble)

| | |
|---|---|
| Board | Hagalu v8.3, the second bench tag |
| Network | Hubble, device "Hagalu-002": AES-128-EAX, counter mode DEVICE_UPTIME, period exponent 15 |
| Made with | `new_hubble_tag.py hagalu_002 hubble-in100-4s-advinterval.cfg --payload sensors`, from Hubble's 4 s sample. `tools/new_hubble_tag.py hagalu_002` with [`configs/hubble-template.cfg`](../configs/hubble-template.cfg) now gives the same file ([how](programming.md#network-payloads)) |
| Advert | every 4 s, 0 dBm, 1 Mbps, channels 37–39, private non-resolvable address renewed every 90 s, XO cap code 8 |
| Payload | encrypted, little-endian: VCC (1 byte, × 0.03125 V), IN100 temperature (2, × 0.01 °C), advert count (4) |
| Private files | `hagalu_002.hubble.key`; `hagalu_002.hubble-sensors.verified-2026-11-20.cfg` (+ `.packet.txt`, `.raw.txt`) |
| Config sha256 | `80c55e3b119e77e2c8e7de9a3a8e5b557cfa24399417cad0933356bd14b170c0` |
| Verified | 20 Nov 2026, from RAM on the adapter: decoded locally (3.406 V, 19.9–20.3 °C, count rising by one per advert) and seen in the Hubble app. A dry run just before burning sent a byte-identical config and image. |
| OTP | burned 20 Nov 2026, 16:44. The tool's record of what it sent is byte-identical to the verified config. |
| On its own | 20 Nov 2026, a walk through town on light only: 25 packets decoded by Hubble; those checked read 1.562 V, 22.3–28.5 °C, advert count 0 ([why 0](roadmap.md#stage-0-bench-work-on-the-v83-boards-now)) |

## gantu_S6_01 (Find My)

| | |
|---|---|
| Board | Hagalu v8.3 S6, the first bench tag |
| Network | Apple Find My, OpenHaystack static key |
| Private files | `gantu_S6_01.keys` |
| Verified | 19 Nov 2026, from RAM: reported by Find My 3 times in 20 min (±76–102 m) |
| On its own | 20 Nov 2026, the same walk: well over a hundred sightings that afternoon, including inside a supermarket |
| OTP | burned before the walk; the config file and its hash weren't recorded. Next time, keep the tool's `nano_beacon_config.cfg` from the burn, as for Hagalu-002. |
