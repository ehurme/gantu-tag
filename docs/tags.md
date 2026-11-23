# Tags

What each programmed tag carries, so a burned tag can be traced back to its configuration. Keys and full `.cfg`
files hold secrets: they stay in the private key folder (`$GANTU_KEYS`; keep a backup) and never go into this repo.
The hash identifies the exact file.

## Hagalu-006 (Find My, S6 comparison pilot)

| | |
|---|---|
| Board | Hagalu v8.3 S6 |
| Network | Apple Find My, OpenHaystack static key, temperature in the status byte (signed × 0.5 °C) |
| Programmed transmit power | **0 dBm** |
| Programmed advertising interval | **3 s (3,000 ms)** |
| OTP record | Burn confirmed by the operator on 22 Nov 2026. NanoBeacon programmer output saved at 21:53 CET. Chip readback is unverified. |
| Programmer output SHA-256 | `270dd06754195cf9d484376d5948f4f75f79134d1deabb6a207fb3e212ced2aa` |
| Observed reception | See [the same-lamp comparison](pi-bench.md#hagalu-006-and-hagalu-003-same-lamp-test). |

## Hagalu-005 (Find My, N6 startup pilot)

| | |
|---|---|
| Board | Hagalu v8.3 N6, the first N6 pilot |
| Network | Apple Find My, OpenHaystack static key |
| Programmed transmit power | **0 dBm** |
| Programmed advertising interval | **3 s (3,000 ms)** |
| Prepared config | `hagalu_005.findmy.cfg`, SHA-256 `4ab34619e48d5e40eefdb04518007398f461fbe5aa2c3f3b1d83892824eac4a6`. The programmer output matches it apart from GUI metadata and the custom UUID field. |
| OTP record | Burn confirmed by the operator on 22 Nov 2026. NanoBeacon programmer output saved at 21:11 CET. Chip readback is unverified. |
| Programmer output SHA-256 | `82d788f32fd6dcc271b788aedf129f45996dff104acf64edc0a32aee988746ad` |
| Status | **Silent since 21:12:07 CET, 22 Nov 2026**, also on the DC boot check; set aside. It is not yet known whether the burned image or the board's own start failed: see [the N6 startup check](pi-bench.md#hagalu-005-n6-startup-check). |

## Hagalu-004 (Find My, field candidate)

| | |
|---|---|
| Board | Hagalu v8.3 S6L |
| Network | Apple Find My, OpenHaystack static key, temperature in the status byte (signed × 0.5 °C) |
| Programmed transmit power | **+4 dBm** |
| Programmed advertising interval | **6 s (6,000 ms)** |
| Prepared config | `hagalu_004.findmy-temp-tx4.cfg` (3 s, +4 dBm), SHA-256 `430a947d00c291818958fc8471c09e7a79bfa1bd8a9ed22058a737fa12ea5c05`. The interval was set to 6 s in the Config Tool before burning. Apart from that, the programmer output differs only in GUI metadata and the custom UUID field. |
| OTP record | Burn reported on 22 Nov 2026. NanoBeacon programmer output saved at 18:34 CET. Chip readback is unverified. |
| Programmer output SHA-256 | `b71e82329b7921cb2de4bbdbaa22906d5766abde4b292dc32ca65e15c57e1621` |
| Verified | 22 Nov 2026, on the Pi. At 19:09 CET, 35 minutes after the burn, the Pi heard it on solar with the temperature decoding. From 20:36:34 to 20:37:56 CET it advertised every 6.0 s, its burned interval ([evidence](pi-bench.md#two-regimes-in-one-run)). |
| Observed solar behavior | See [the solar ramp and window test](pi-bench.md#hagalu-003-and-hagalu-004-solar-bench-22-november-2026). |

## Hagalu-003 (Find My)

| | |
|---|---|
| Board | Hagalu v8.3 S6L, third programmed PCBA |
| Network | Apple Find My, OpenHaystack static key, temperature in the status byte (signed × 0.5 °C) |
| Prepared config | `hagalu_003.findmy-temp.cfg` at 0 dBm, SHA-256 `59324deb53b326fd550c20a8af05fde92723a085192c436129251aa56470395e` |
| OTP | 22 Nov 2026, tool output saved at 16:59 CET. The saved config matches the prepared variant apart from GUI metadata and the custom UUID field. |
| Programmer output SHA-256 | `1a67bfbc62d650f3a9df800f8e72e1a0b8c0882dffb7933d75d5aa970f38be1d` |
| Verified | 22 Nov 2026, 17:08–17:09 CET. The Pi received nine matching BLE advertisements. The last was at 17:09:34 CET and read −62 dBm and 21 °C. |

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

## Hagalu-001 (Find My)

| | |
|---|---|
| Board | Hagalu v8.3 S6, the first bench tag. Burned as `gantu_S6_01`. |
| Network | Apple Find My, OpenHaystack static key |
| Private files | `gantu_S6_01.keys` |
| Verified | 19 Nov 2026, from RAM: reported by Find My 3 times in 20 min (±76–102 m) |
| On its own | 20 Nov 2026, the same walk: well over a hundred sightings that afternoon, including inside a supermarket |
| OTP | burned before the walk; the config file and its hash weren't recorded. Next time, keep the tool's `nano_beacon_config.cfg` from the burn, as for Hagalu-002. |

## Hagalu-007 to Hagalu-020 (prepared Find My configs)

Made on 21 Nov 2026 with `tools/new_findmy_tag.py hagalu_003` … `hagalu_020`, from
[`configs/findmy-template.cfg`](../configs/findmy-template.cfg): Find My, every 3 s, 0 dBm, XO cap code 8. Each key pair
was checked against its config and registered on the dashboard. Private files: `hagalu_NNN.keys` and
`hagalu_NNN.findmy.cfg`. The board column is the plan (it assumes Hagalu-002 is an S6); when a tag is burned, it gets
its own section above with the board actually used. Why each variant: [roadmap](roadmap.md#what-each-variant-tests).

| Tag | Planned board | Purpose | Config sha256 |
|---|---|---|---|
| Hagalu-007 | S6 | +4 dBm tried in RAM first; burn after | `20869dbca9b5a33c5088f02c8acc38dcd4410485086cf07c1527d024606efdfd` |
| Hagalu-008 | S6 | field tag | `5e9bef33583fdd34ad6e33c14110a7df433242847c4a5d3d98cef5abdd1705ed` |
| Hagalu-009 | S6 | field tag | `8695fe240b321d6c931e02a57e0fc4ca8e18795f3217ab59009dede911aeb1ec` |
| Hagalu-010 | S6 | field tag | `9903593ab791f2ae6425965552a2cb9a3776dcc7422c45d9a7c5cfdd1fe266ac` |
| Hagalu-011 | S6 | field tag | `9bf9ce38f3c7aa2ba2ae7732583b95719628327db637f969662d9f6fb92e4c40` |
| Hagalu-012 | S6L | hold for Hagalu-003 and -004 | `6b6f46103eb6faae4e103dbe752644506b48e2e6d13eff2cbe3b88085156bf6f` |
| Hagalu-013 | S6L | hold for Hagalu-003 and -004 | `20e985a13a185dfe190982e0fbc10867ce3c5cb68cdd4995d7c241f4f6d36458` |
| Hagalu-014 | S6L | hold for Hagalu-003 and -004 | `9996bfee6a3cd8a47d963636f3328c4d5d1d14946e665d96eef8a1c3a8f221ef` |
| Hagalu-015 | S6L | hold for Hagalu-003 and -004 | `b6fa073a4fa7cde12026d551650d19ea9cd2c3edf2386fea20747b95dcde63d6` |
| Hagalu-016 | S6L | hold for Hagalu-003 and -004 | `f68ca52ee96595036747fd9ee8c01351ca35fe84dac584e816c42a7d8d86ee62` |
| Hagalu-017 | S6L | hold for Hagalu-003 and -004 | `3315fa8d883a30b704f40a6adb4454a09572c751c63909ffaa053a8e9b1da636` |
| Hagalu-018 | N6 | on hold: Hagalu-005 (N6) went silent after its burn | `ea0c45cd3f4a19e7e7deb519d616a6f24e28e85d7b7ded64f87d339d1163387a` |
| Hagalu-019 | N6 | on hold: Hagalu-005 (N6) went silent after its burn | `3ade18b06fa0f366c406c230d7d3281fc06bc385107667d94c80722d533f3dbb` |
| Hagalu-020 | N6 | on hold: Hagalu-005 (N6) went silent after its burn | `c6949ce15871f1701122f9a61cf3ae6489fb09947aae4c1148b0a0cb04924fd1` |

Don't burn another N6 until [the Hagalu-005 check](pi-bench.md#hagalu-005-n6-startup-check) shows why it went silent.
