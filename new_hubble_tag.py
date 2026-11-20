#!/usr/bin/env python3
"""Make a Hubble Network .cfg for one gantu tag, for InPlay's NanoBeacon Config Tool.

Usage:  python3 new_hubble_tag.py hagalu_002 hubble-in100-4s-advinterval.cfg [--payload sensors|ff]
                                  [--interval 4] [--period-exponent 15] [--tx 0]

The second argument is Hubble's own sample config, from
https://github.com/HubbleNetwork/hubble-inplay-cfg/tree/main/samples (any interval: this script sets it).
It is not copied into this repo because that repository has no licence.

Register the device with Hubble first (AES-128-EAX, counter mode DEVICE_UPTIME, the same period exponent) and
paste its key when asked (32 hex characters or base64; it is not echoed). Writes (never overwrites), mode 600:
  ~/Documents/KiCad/gantu_keys/<name>.hubble.key   key + settings (KEEP PRIVATE, never commit)
  ~/Documents/KiCad/gantu_keys/<name>.hubble.cfg   load this in the Config Tool (it contains the key too)

Payloads (AES-EAX encrypted, little-endian), see docs/programming.md:
  ff       1 byte  0xFF                          (Hubble's own default)
  sensors  7 bytes VCC (1) + temperature (2) + advertising count (4)
Same maths as Hubble's hubble-inplay-cfg (build_config); stdlib only.
"""
import argparse, base64, binascii, getpass, json, os, sys

KEYS_DIR = os.path.expanduser("~/Documents/KiCad/gantu_keys")
TIMER = "write: 3 1 3 3284 "          # EID timer: adverts until the 128-period EID pool wraps
PREFIX = "0303a6fc"                    # complete list of 16-bit service UUIDs: 0xFCA6
HEAD = "16a6fc08<SALT 2byte 0 0><EID 8byte 1 0>"
TAIL = "<TAG 4byte 0 0>"
PAYLOADS = {  # token string, encrypted bytes
    "ff": ("<EncRaw FF 1byte 0 1>", 1),
    "sensors": ("<VCC 1byte 0 1><TEMP 2byte 0 1><ADVCNT 4byte 0 1>", 7),
}


def read_key():
    raw = (getpass.getpass("Hubble AES-128 key (hex or base64): ") if sys.stdin.isatty()
           else sys.stdin.readline()).strip()
    try:
        key = bytes.fromhex(raw) if len(raw) == 32 else base64.b64decode(raw, validate=True)
    except (ValueError, binascii.Error):
        sys.exit("key is neither 32 hex characters nor base64")
    if len(key) != 16:
        sys.exit(f"key must be 16 bytes, got {len(key)}")
    return key


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("name")
    ap.add_argument("template", help="Hubble sample .cfg (hubble-inplay-cfg/samples)")
    ap.add_argument("--payload", choices=PAYLOADS, default="sensors")
    ap.add_argument("--interval", type=int, default=4, help="seconds (default 4)")
    ap.add_argument("--period-exponent", type=int, default=15, choices=range(10, 16),
                    help="EID rotation 2^n s; must match the Hubble registration (default 15)")
    ap.add_argument("--tx", type=int, default=0, choices=range(-4, 5), help="dBm (default 0)")
    ap.add_argument("--out-dir", default=KEYS_DIR)
    a = ap.parse_args()

    key_path = os.path.join(a.out_dir, f"{a.name}.hubble.key")
    cfg_path = os.path.join(a.out_dir, f"{a.name}.hubble.cfg")
    for p in (key_path, cfg_path):
        if os.path.exists(p):
            sys.exit(f"{p} already exists - pick another name (one key per tag).")

    cfg = json.load(open(a.template))
    adv, regs = cfg["advSet"][0], cfg["regSettingCust"]
    if not adv["payload"][0]["data"].startswith(PREFIX) or not any(r.startswith(TIMER) for r in regs):
        sys.exit(f"{a.template} doesn't look like a Hubble IN100 sample config")
    key = read_key()

    tokens, n = PAYLOADS[a.payload]
    adv["payload"][0]["data"] = PREFIX + f"{18 + n:02X}" + HEAD + tokens + TAIL
    adv["payload"][0]["len"] = 23 + n                      # 31-byte advert limit: n <= 8
    adv["interval"] = a.interval * 1000
    adv["rot_exp"] = a.period_exponent
    cfg["txSetting"].update(key0=key.hex(), txPower=a.tx,
                            xoCap=8)  # cap code that works on the v8.3 boards (Hubble's template: 7)
    count = (2 ** a.period_exponent * 127 * 1000) // (a.interval * 1000)
    regs[next(i for i, r in enumerate(regs) if r.startswith(TIMER))] = TIMER + f"{count:x}"

    os.makedirs(a.out_dir, exist_ok=True)
    old = os.umask(0o077)
    with open(key_path, "w") as f:
        f.write(f"# gantu tag {a.name} - Hubble AES-128 key (AES-128-EAX, DEVICE_UPTIME). KEEP PRIVATE.\n"
                f"key_hex: {key.hex()}\nkey_b64: {base64.b64encode(key).decode()}\n"
                f"period_exponent: {a.period_exponent}\ninterval_s: {a.interval}\ntx_dbm: {a.tx}\n"
                f"payload: {a.payload}\n")
    with open(cfg_path, "w") as f:
        json.dump(cfg, f, indent=4)
    os.umask(old)

    print(f"""
Tag: {a.name}   payload: {a.payload} ({n} encrypted bytes)   interval {a.interval} s   2^{a.period_exponent} s rotation   {a.tx} dBm
Key file: {key_path}
Config:   {cfg_path}

NanoBeacon Config Tool: Load the config, power-cycle the tag, Probe and Connect at once, Run in RAM.
Leave the format on "Custom" (the tool's own "Hubble" format sends the payload unencrypted).
Check: python3 hubble_decode.py {key_path} <service data hex of UUID 0xFCA6>
""")


if __name__ == "__main__":
    main()
