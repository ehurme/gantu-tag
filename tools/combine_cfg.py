#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Pavan Kumar Kaushik. Part of gantu-tag, https://github.com/pvnkmrksk/gantu-tag (see NOTICE).
"""Put two single-set configs into one, as advertising sets #1 and #2 (EXPERIMENTAL: RAM-test it first).

Usage:  python3 tools/combine_cfg.py FIRST.cfg SECOND.cfg -o OUT.cfg [--interval1 S] [--interval2 S]
                                     [--channels1 37,38,39] [--channels2 37,38,39]

The IN100 runs up to three advertising sets, each with its own address, payload, interval and channels, so one tag
can advertise on Find My and on Hubble. The first file's set becomes #1, the second's #2.

Channels: each set's "chCtrl" is a mask of advertising channels it SKIPS (bit 0 = 37, bit 1 = 38, bit 2 = 39; 0 = all
three), as the Config Tool wrote it on 21 Nov 2026 for "37 only" (6) and "38 + 39" (1). An advert's charge grows with
its channels (about 5 µC each at 0 dBm), so fewer channels per set keeps two sets within one set's energy.

What the two files share is global on the chip, so they must agree: TX power, crystal trim, channel map and the
on-chip measurement units (vccUnit, tempUnit). A Hubble config also brings global parts that only it uses (key0,
its custom register writes for the rotating ID, regValTrigEn): those are taken from whichever file has them.
Two Hubble configs can't be combined (one key0, one set of rotation registers).

Checked in RAM on the adapter (Hagalu-006, 21 Nov 2026; Find My #1 every 3 s, Hubble #2 every 10 s): both sets
advertise and both networks reported them; Hubble decodes as set #2; each set keeps its own advert count (Hubble's
rose by one per Hubble advert), so Find My doesn't disturb Hubble's EID timer. The two schedules don't lock: each
advert is jittered by tens of ms, so they slide past each other (closest pair in 150 s: 13.5 ms, both received).

Power-up (same test, recorded on the Pi): the IN100 sends BOTH sets at once, back to back (Hubble #2 then Find My #1,
2.5 ms apart). And that first Hubble advert, with Hubble as set #2, is encrypted with an all-zero key (ID and payload),
so Hubble can't decode it; from the second advert on the key is right. Hubble as set #1 decoded on its first advert
(Hagalu-002). So on Hagalu, where every advert in dim light follows a fresh power-up:
  - two 3-channel adverts per start can take VCC below 1.1 V and lock the tag until dark;
  - with Hubble as set #2, every Hubble advert would be one of those undecodable first ones.
Put Hubble first, and on Hagalu test one channel per set before burning. On Irulu only one advert is lost, once.

Update, same evening, three power-ups with Hubble as set #1: its first advert was ALSO zero-key (2 of 2 caught), and
set #2 still went first (Find My, 1.6 ms before Hubble). So the set order doesn't fix it. Hagalu-002 (Hubble alone,
burned) decoded its first adverts, so either "Run in RAM" starts advertising before the key is in place, or two sets
cause it. Then Hubble ALONE in RAM: zero-key first advert in 3 of 3 power-ups. So it's the RAM path, not the second
set: a burned tag boots with its key (as Hagalu-002 shows). Confirm after burning: power-cycle on the adapter and
check that the first Hubble advert (count 0) decodes.
"""
import argparse, json, os, sys

SHARED_TX = ("txPower", "txPaGain", "sleepAftTx", "uartSingleWire", "uartPinSel", "xoCap", "xoStableTime", "xoGm",
             "ch0", "ch1", "ch2")


def is_hubble(cfg):
    """A Hubble config carries rotation register writes (and, once keyed, a non-zero key0)."""
    return bool(cfg.get("regSettingCust")) or bool(set(cfg["txSetting"].get("key0", "")) - {"0"})


def channel_mask(channels):
    """'38,39' -> chCtrl: the channels to skip, bit 0 = 37, bit 1 = 38, bit 2 = 39."""
    use = {int(c) for c in channels.split(",")}
    if not use or use - {37, 38, 39}:
        sys.exit(f"channels must be a non-empty subset of 37,38,39, got {channels!r}")
    return sum(1 << (c - 37) for c in (37, 38, 39) if c not in use)


def combine(first, second, interval1=None, interval2=None, channels1=None, channels2=None):
    if len(first["advSet"]) != 1 or len(second["advSet"]) != 1:
        sys.exit("each input must have exactly one advertising set")
    hub = [c for c in (first, second) if is_hubble(c)]
    if len(hub) > 1:
        sys.exit("both inputs are Hubble configs: the chip has one key0 and one set of rotation registers")
    for k in SHARED_TX:
        if first["txSetting"].get(k) != second["txSetting"].get(k):
            sys.exit(f"txSetting.{k} differs ({first['txSetting'].get(k)} vs {second['txSetting'].get(k)}): it is global")
    for k in ("vccUnit", "tempUnit"):
        if first.get(k) != second.get(k):
            sys.exit(f"{k} differs ({first.get(k)} vs {second.get(k)}): the on-chip units are global")
    # Everything that isn't per set must be identical, apart from the Hubble-only parts handled below.
    skip = {"advSet", "txSetting", "regSettingCust", "regValTrigEn", "guiRuntimeCfg"}
    for k in (set(first) | set(second)) - skip:
        if first.get(k) != second.get(k):
            sys.exit(f"global setting {k!r} differs between the two files")

    # Hubble's EID timer register is counted in adverts and computed from its interval by new_hubble_tag.py.
    for cfg, override, n in ((first, interval1, 1), (second, interval2, 2)):
        if override and is_hubble(cfg):
            sys.exit(f"set #{n} is Hubble: make it with new_hubble_tag.py --interval instead (its EID timer depends on it)")
    out = json.loads(json.dumps(hub[0] if hub else first))      # Hubble's globals, if any
    a, b = (json.loads(json.dumps(c["advSet"][0])) for c in (first, second))
    a["id"], b["id"] = 0, 1
    if interval1:
        a["interval"] = int(interval1 * 1000)
    if interval2:
        b["interval"] = int(interval2 * 1000)
    if channels1:
        a["chCtrl"] = channel_mask(channels1)
    if channels2:
        b["chCtrl"] = channel_mask(channels2)
    out["advSet"] = [a, b]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("first"), ap.add_argument("second")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--interval1", type=float, help="set #1 interval in s (default: as in FIRST)")
    ap.add_argument("--interval2", type=float, help="set #2 interval in s (default: as in SECOND)")
    ap.add_argument("--channels1", help="set #1 advertising channels, e.g. 37 or 38,39 (default: as in FIRST)")
    ap.add_argument("--channels2", help="set #2 advertising channels (default: as in SECOND)")
    a = ap.parse_args()
    if os.path.exists(a.out):
        sys.exit(f"{a.out} already exists")
    out = combine(json.load(open(a.first)), json.load(open(a.second)), a.interval1, a.interval2,
                  a.channels1, a.channels2)
    old = os.umask(0o077)
    with open(a.out, "w") as f:
        json.dump(out, f, indent=4)
    os.umask(old)
    for s in out["advSet"]:
        chans = ",".join(str(c) for c in (37, 38, 39) if not s.get("chCtrl", 0) >> (c - 37) & 1)
        print(f"set #{s['id'] + 1}: {s['addrType']:<14} every {s['interval'] / 1000:g} s on {chans}, "
              f"payload {s['payload'][0]['data'][:40]}…")
    print(f"wrote {a.out}  (RAM test only until both sets have been seen and decoded)")


if __name__ == "__main__":
    main()
