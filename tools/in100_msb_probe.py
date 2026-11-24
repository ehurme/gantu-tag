#!/usr/bin/env python3
"""Write a key-free IN100 RAM test for SRAM or GPIO counter byte selection."""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="new .cfg file")
    probe = parser.add_mutually_exclusive_group()
    probe.add_argument("--value", type=lambda value: int(value, 0),
                       help="unsigned 16-bit SRAM word (default: 0x1234)")
    probe.add_argument("--gpio-edge", action="store_true",
                       help="compare full and one-byte rising edge counts on GPIO2")
    args = parser.parse_args()
    value = 0x1234 if args.value is None else args.value
    if not 0 <= value <= 0xFFFF:
        parser.error("--value must be between 0 and 0xffff")
    if args.output.suffix.lower() != ".cfg":
        parser.error("output must end in .cfg")

    template = Path(__file__).resolve().parents[1] / "configs" / "findmy-template.cfg"
    cfg = json.loads(template.read_bytes())
    adv, = cfg["advSet"]
    cfg["regSetting"] = []
    cfg["guiRuntimeCfg"] = "tx_interval_max=30000;"
    if args.gpio_edge:
        cfg["regSettingCust"] = []
        cfg["edgeCount"] = {
            "enable": 1, "srcPin": 2, "countEdge": 1,
            "clearByTx": 0, "clearBySleep": 0, "clearByEvent": 0,
        }
        gpio2 = next(pin for pin in cfg["gpio"] if pin["id"] == 2)
        gpio2.update({"digital": "ie", "pu-pd": 2, "latch": 1})
        adv["payload"] = [{
            "len": 9,
            "type": 255,
            "data": "ffff5b<EDGE 3byte 0 0><EDGE 1byte 0 0><EDGE 1byte 1 0>",
        }]
    else:
        cfg["regSettingCust"] = [f"write: 3 1 3 2f80 {value:08x}"]
        adv["payload"] = [{
            "len": 10,
            "type": 255,
            "data": (
                "ffff5a"
                "<REG2f80 2byte 0 0><REG2f80 2byte 1 0>"
                "<REG2f80 1byte 0 0><REG2f81 1byte 0 0>"
            ),
        }]

    try:
        with args.output.open("x", encoding="utf-8") as output:
            json.dump(cfg, output, indent=2)
            output.write("\n")
    except FileExistsError:
        parser.error(f"output already exists: {args.output}")

    if args.gpio_edge:
        print("Manufacturer AD structure: 09 ff ff ff 5b <count LE, 3 B> <LE, 1 B> <BE, 1 B>")
    else:
        low, high = value.to_bytes(2, "little")
        manufacturer_data = bytes((0xFF, 0xFF, 0x5A, low, high, high, low, low, high))
        print(f"Expected manufacturer AD structure: 0a ff {manufacturer_data.hex(' ')}")


if __name__ == "__main__":
    main()
