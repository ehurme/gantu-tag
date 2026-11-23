# Gantu tag

- **Check a tag on the bench.** Read [the Pi bench runbook](docs/pi-bench.md). Start with Gantumoote’s Flash history and the Pi BLE service. Use local BLE evidence to confirm the radio after an OTP burn.
- **Program a tag.** Read [the programmer steps](docs/programming.md) and [the tag register](docs/tags.md). Match the physical PCBA marking to the next serial and save the tool’s output immediately after burning.
- **Handle keys.** Keep per-tag configs, keys and raw programmer evidence on the Pi under Gantumoote’s private data directory or in the ignored local key folder. Publish the serial, board, network and SHA-256.
