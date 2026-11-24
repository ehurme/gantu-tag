# Config templates

Two ready-made configurations for InPlay's NanoBeacon Config Tool, one per network. They work on both tags
(Hagalu and Irulu) and are identical to configurations that ran on real tags, except that **the key is zeroed**.
Adding your key is the only change you need to make.

| File | Network | Advert | Key goes in |
|---|---|---|---|
| [`findmy-template.cfg`](findmy-template.cfg) | Apple Find My (OpenHaystack static key) | every 3 s, 0 dBm, static random address | the address and the advert bytes (derived from the key) |
| [`hubble-template.cfg`](hubble-template.cfg) | Hubble Network (AES-128-EAX, DEVICE_UPTIME, period exponent 15) | every 4 s, 0 dBm, encrypted VCC + temperature + advert count | `"key0"` (32 hex characters) |

Both use XO cap code 8, which worked on the v8.3 boards, a 1 Mbps PHY and all three advertising channels.

## Where the key comes from

- **Find My:** you make the key pair yourself; Apple never issues one. Run `python3 tools/new_findmy_tag.py <name>`
  (or use OpenHaystack). Keep the **private key**: it's the only way to decrypt the location reports later.
  The tag carries only the public (advertisement) key.
- **Hubble:** register a device in the Hubble dashboard (or its API) with encryption **AES-128-EAX**, counter mode
  **DEVICE_UPTIME** and period exponent **15**. Hubble shows the device's 16-byte key, as hex or base64. The three
  settings must match the template exactly, or Hubble silently drops the packets.

## Three ways to add the key

1. **On the website**, no install: [pvnkmrksk.github.io/gantu-tag/guide.html#configure](https://pvnkmrksk.github.io/gantu-tag/guide.html#configure).
   Paste the key and download a finished `.cfg`. Everything happens in your browser; the key isn't sent anywhere.
2. **With the scripts** (Python 3), which also keep a private record of each tag's key:
   ```
   python3 tools/new_findmy_tag.py hagalu_03            # new Find My key pair + hagalu_03.findmy.cfg
   python3 tools/new_hubble_tag.py hagalu_002           # asks for the Hubble key, writes hagalu_002.hubble.cfg
   ```
   Files go to `$GANTU_KEYS` (default `~/gantu-keys/`), never into this repo. The `.gitignore` refuses `*.cfg`,
   `*.key` and `*.keys` anywhere except these two templates.
3. **By hand:**
   - Hubble: open `hubble-template.cfg` in a text editor and replace the 32 zeros in `"key0"` with your key in hex.
     If Hubble gave you base64, convert it first: `echo '<base64>' | base64 -d | xxd -p`.
   - Find My: the key is split across the address and the advert bytes, with bit operations, so use the website
     or the script. Or type the fields into the Config Tool as described in
     [`docs/programming.md`](../docs/programming.md#network-payloads).

Then load the `.cfg` in the Config Tool, test it in RAM, and burn it: see the
[build guide](../docs/guide.md#6-program-the-tag).

The [IN100 CFG reference](../docs/in100-config.md) maps the UI to JSON and includes a key-free register byte-selection probe.

## Checked

- `tools/new_hubble_tag.py` with Hagalu-002's key turns `hubble-template.cfg` into the config burned into that tag
  on 20 Nov 2026, byte for byte (sha256 `80c55e3b…`, see [`docs/tags.md`](../docs/tags.md)).
- `tools/new_findmy_tag.py --adv-key` with hagalu_03's advertisement key turns `findmy-template.cfg` into the
  config the Config Tool saved for that tag, byte for byte.

`hubble-template.cfg` is the Config Tool's own record of the Hagalu-002 configuration. Its Hubble-specific parts
(the advert layout and the register writes for the rotating ID) follow Hubble's published IN100 sample configs in
[HubbleNetwork/hubble-inplay-cfg](https://github.com/HubbleNetwork/hubble-inplay-cfg).
