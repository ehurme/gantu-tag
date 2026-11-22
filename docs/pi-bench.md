# Pi bench

## Check BLE

The receiver runs on `walk-pi5` as `gantumoote-ble.service`. Open **Devices & connections → Flash history & Pi BLE** in Gantumoote to see the last local reception and download a 24-hour CSV. A Find My or Hubble location report in the map is a separate network observation.

From the Pi checkout:

```sh
cd ~/gantumoote
systemctl status gantumoote-ble --no-pager
journalctl -u gantumoote-ble -n 25 --no-pager
ls -lh ~/blelog
/usr/bin/python3 -m dashboard.ble capture ~/blelog/burn.btsnoop
```

The `burn.btsnoop` capture spans 12:09–12:29 CET on 22 Nov 2026. A second capture covers 16:42:27–16:42:47 CET, before Hagalu-003’s recorded OTP output. The 17:08–17:09 CET capture contains nine matching Hagalu-003 Find My adverts. The filename and modification time alone do not establish the capture window.

## Program the next PCBA

1. Read the variant printed under the board. The next prepared S6L is Hagalu-004. In Gantumoote’s Flash history, download `findmy-temp-tx4.cfg` under that serial and use its own key.
2. Follow [the programmer steps](programming.md#steps). After a successful OTP write, save the tool’s emitted `nano_beacon_config.cfg` and the matching packet and raw dumps before running the tool again. On the Mac they appear in `~/Library/Logs/nanobeacon/`.
3. Archive the exact tool output on the Pi using [Gantumoote’s flash command and sealing steps](https://github.com/pvnkmrksk/gantumoote#flash-history-and-pi-ble). Check the displayed record, compare its SHA-256 to the local file and confirm a local BLE reception after power-cycling. Record the board, network and hash in [the tag register](tags.md).
