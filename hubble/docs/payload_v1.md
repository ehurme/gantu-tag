# gantu Hubble payload, format v1 (13 bytes)

Hubble lets each advert carry up to 13 bytes of custom data, encrypted by the Hubble SDK. These 104 bits are packed
MSB-first, in this order:

| # | Field | Bits | Encoding | Range / resolution | "No data" |
|---|---|---|---|---|---|
| 1 | `version` | 3 | 1 for this format | | |
| 2 | `alive` | 1 | 1 if any **active minute** in the last 24 h | | |
| 3 | `inactive_h` | 7 | whole hours since the last active minute | 0–126 h | 127 (≥ 127 h, or never) |
| 4 | `vedba_cum` | 24 | **cumulative** VeDBA since start-up, 0.1 g·s per count, wraps at 2²⁴ | 1.68 × 10⁶ g·s before wrap | |
| 5 | `temp` | 8 | (T + 20 °C) / 0.25 °C | −20.00 … +43.50 °C, 0.25 °C | 255 |
| 6 | `temp_min24` | 8 | as `temp`: minimum of the samples in the last 24 h | | 255 |
| 7 | `pressure` | 13 | (P − 300 hPa) / 0.1 hPa | 300.0 … 1119.0 hPa, 0.1 hPa (≈ 0.8 m) | 8191 |
| 8 | `pressure_min24` | 13 | as `pressure`: minimum in the last 24 h (≈ highest point reached) | | 8191 |
| 9 | `pressure_min24_age_h` | 5 | hours since that minimum was recorded | 0–23 h | 31 |
| 10 | `light` | 6 | top 6 bits of the 12-bit ADC reading on the light sensor | 0–63 (calibrate to lux) | |
| 11 | `battery` | 5 | (V − 2.00 V) / 0.05 V | 2.00 … 3.55 V | 0 |
| 12 | `counter` | 8 | +1 for every new payload, wraps | 0–255 | |
| 13 | reserved | 3 | 0 | | |

## Definitions (what the tag computes)

- **VeDBA.** Each accelerometer sample `a` (mg, 3 axes) has its static part removed: a running mean per axis with
  a time constant of ≈ 2 s (an EMA of 2^k samples). The sample's VeDBA is |a − static|, and the tag integrates it
  over time:
  - 1 count = 0.1 g·s = 0.98 m s⁻² · s;
  - divide the change between two messages by the elapsed time to get mean VeDBA in g;
  - the cumulative counter means a missed message loses nothing. Use `gantu_vedba_diff()` (R) or `vedba_diff()`
    (Python), which handle the wrap.
  - Sensor noise adds ≈ 1–2 mg at rest, about 0.1–0.2 g·s per 100 s. Subtract it as a baseline taken from
    resting periods.
- **Active minute:** a minute whose mean VeDBA is above 30 mg (`active_mg`, set at build time).
  - `alive` is 1 if there has been at least one active minute in the last 24 h (`alive_window_h`).
  - `inactive_h` says how long the tag has been still. A dead or dropped tag shows `alive = 0` and an
    `inactive_h` that keeps climbing.
- **24 h minima.** Pressure and temperature are sampled every 5 min. The tag keeps the minimum per clock hour for
  24 hours, and reports the smallest of those bins, plus the age of the pressure minimum in hours.
  - The pressure minimum marks the highest altitude of the last day.
  - The temperature minimum marks torpor.
- **Light.** The raw ADC voltage of an LED (or photodiode) used as a photovoltaic sensor. Its open-circuit voltage
  rises roughly with log(light), so the code is already a log-light scale. Calibrate it per LED colour against a lux
  meter.
- **Timing.** The payload refreshes every 5–15 min and is re-advertised every few seconds in between. When a
  message arrived comes from Hubble's backend (gateway time). `counter` and `vedba_cum` let you order messages and
  spot gaps.

## Decoders and tests

- C encoder: [`../firmware/core/gantu_core.c`](../firmware/core/gantu_core.c) (`gantu_pack_payload`).
- Python: [`../tools/gantu_payload.py`](../tools/gantu_payload.py). Use `decode(hex)`, or run it from the command
  line on a CSV.
- R: [`../R/decode_gantu_payload.R`](../R/decode_gantu_payload.R). `decode_gantu_payload(hex_vector)` returns a
  data.frame, and `gantu_vedba_diff()` turns the cumulative counter into per-interval VeDBA.
- Tests:
  ```sh
  make -C hubble/firmware/test run            # simulates 3 nights of a bat; writes payloads.csv
  python3 hubble/tools/test_decoders.py       # Python vs C
  Rscript hubble/tools/test_decoders.R        # R vs C
  ```
  All three agree on all 408 simulated payloads.

## Changing the format

Bump `version` and keep v1 decodable: the decoders refuse unknown versions rather than guessing. The 3 reserved bits
are the first place to add a flag, for example "pressure sensor fault".
