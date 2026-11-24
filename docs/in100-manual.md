# IN100 payload byte selection and scaling

For Advanced controls, command syntax, and the runnable SRAM fixture, see the [IN100 CFG reference](in100-config.md).

## Transmitting the high byte

The IN100 Config Tool compiles Register Read Data to a **byte address and a byte count**. To select the high byte of a little-endian 16-bit value in SRAM at `0x2F80`, use `<REG2f81 1byte 0 0>` in `advSet[].payload[].data`. The address is hexadecimal. The final two arguments select big-endian byte order and encryption, respectively. `0` disables the option. Adjust the enclosing payload `len` for the emitted byte count. The examples below reproduce the installed macOS compiler's output. An over-the-air check of the SRAM example and the internal register candidates is pending.

| Payload token | Compiled field descriptor, hex | Source address encoded |
| --- | --- | --- |
| `<REG2f80 2byte 0 0>` | `1f 02 80 2f` | `0x2F80`, little endian |
| `<REG2f80 2byte 1 0>` | `3f 02 81 2f` | `0x2F81`, big endian |
| `<REG2f80 1byte 0 0>` | `1f 01 80 2f` | `0x2F80`, little endian |
| `<REG2f80 1byte 1 0>` | `3f 01 80 2f` | `0x2F80`, big endian |
| `<REG2f81 1byte 0 0>` | `1f 01 81 2f` | `0x2F81`, little endian |
| `<REG61d 1byte 0 0>` | `1f 01 1d 06` | `0x061D`, ADC0 candidate |
| `<REG73d 1byte 0 0>` | `1f 01 3d 07` | `0x073D`, temperature candidate |
| `<I2C1R1 1byte 0 0>` | `1f 01 01 23` | `0x2301`, I²C slave 1 offset 1 |

The compiler emits source type `0x1F` for both plain `REG` and `I2C<n>R<offset>`. Its big-endian path starts at `base + count − 1`. With a byte count of one, either endian setting starts at `base`. The installed macOS picker disables the Big Endian control for `REG` and I²C read-data sources, while the CFG compiler honors the bit. The I²C offset is decimal and selects the position of the sensor byte in storage. For an MSB-first sensor sending `12 34`, use offset `0`, and for an LSB-first sensor sending `34 12`, use offset `1`. The tool uses 16-byte strides at `0x2300`, `0x2310`, and `0x2320`, matching Figure 41 in the guide. The cached-data article's prose uses `0x2316` and `0x2332` for the last two, which conflict with those 16-byte strides. [InPlay Config Tool User Guide v1.06, §2.4](https://www.manualslib.com/manual/3441367/Inplay-Nanobeacon-In100.html?page=41), [InPlay cached-data application note](https://github.com/NanoBeacon/config-files/tree/main/Store%20Cached%20Data).

InPlay publishes ADC result addresses `0x061C`, `0x063C`, `0x065C`, and `0x067C`, plus temperature at `0x073C`, for the register copy engine. For an internal register, compare the ordinary two-byte field with `REG<address> 2byte`, then check `REG<address+1> 1byte` against its high byte. The compiler preserves odd addresses, and a BLE capture can establish what the peripheral register bus returns. If the direct peripheral read behaves differently, the vendor's word-copy engine provides a route through byte-addressed SRAM. [InPlay cached-data application note, ADC and temperature examples](https://github.com/NanoBeacon/config-files/tree/main/Store%20Cached%20Data#adc-data-example), [IN100 datasheet, §3.5.3](https://inplay-tech.com/IN100_datasheet.pdf#page=19).

## Choosing the one-byte encoding

| Source | Available encoding | Consequence for range and precision |
| --- | --- | --- |
| 16-bit unsigned data | Select the high byte from its byte address | `0x1234` yields `0x12`. This encodes `floor(value / 256)` and covers the full input range in buckets 256 codes wide. |
| 16-bit signed temperature at `0.01 °C/LSB` | Select the high byte and decode as signed | Each step is `2.56 °C`, rounded down to the next bucket in the original scale. For a `1 °C` step, top-level `"tempUnit": 1.0` and `<TEMP 1byte 0 0>` use the vendor's documented unit mapping. The signed one-byte result represents `−128` to `127 °C`. |
| 11-bit raw ADC | Coarsen via channel unit mapping, then test a one-byte ADC token | Extracting the 16-bit container's high byte retains three bits of an 11-bit raw code. An eightfold reduction retains eight bits. Default nominal `0.78125 mV/LSB × 8 = 6.25 mV/LSB`; allow headroom for calibration and quantization. |
| 32-bit advertising counter | Choose 1–4 payload bytes | The guide explicitly uses the least-significant bytes. A one-byte count rolls over every 256 advertising events, and a two-byte count every 65,536 events. At a nominal 4 s interval that is about 17 minutes and 3.03 days, respectively. |

Temperature mapping and counter truncation are documented. The ADC unit map uses `adc[].unitLsb`, `valueV04` for the physical value at 0.4 V and `valueV14` at 1.4 V. Thresholds on mapped ADC channels compare the mapped code, so update ADC thresholds and the receiver scale when changing units. The app computes the ADC-specific fixed-point gain, shift, signed offset and negative clipping from the calibration data and this map. The ADC result is signed 16-bit. For a one-byte signed receiver keep the mapped integer within `−128…127`; when the physical range is nonnegative, the receiver may instead interpret `0…255` as unsigned. The picker fixes ADC payload width at two bytes, but a hand-edited `<ADC CH0 1byte 0 0>` passes the validator and generates `05 00` in place of `05 10` for two bytes. Bench-check the resulting code width and mapped endpoints before adopting that form. [InPlay Config Tool User Guide v1.06, ADC unit mapping](https://www.manualslib.com/manual/3441367/Inplay-Nanobeacon-In100.html?page=36), [temperature units](https://www.manualslib.com/manual/3441367/Inplay-Nanobeacon-In100.html?page=15), [counter truncation](https://www.manualslib.com/manual/3441367/Inplay-Nanobeacon-In100.html?page=17), [IN100 datasheet, §4.4](https://inplay-tech.com/IN100_datasheet.pdf#page=22).

Selecting a payload byte narrows data that the chip has already computed. Any overflow in the ADC's mapped result occurs earlier, so design the mapping to fit across the input range. The tool provides timed writes, masked writes, delays, register copies via dedicated hardware, and byte selection. A general-purpose register shift or arithmetic opcode remains unverified. The packet format includes an `msb lsb select` field, and this compiler sets it for authentication tags. The CFG parser leaves that field at zero for `REG`, ADC, temperature and counters. [InPlay Config Tool User Guide v1.06, Advanced Settings](https://www.manualslib.com/manual/3441367/Inplay-Nanobeacon-In100.html?page=47), [InPlay cached-data application note](https://github.com/NanoBeacon/config-files/tree/main/Store%20Cached%20Data).

## Payload entries beyond the guide

These observations come from running the installed tool's payload validator and field compiler. The macOS compiler identity is the `IN100ConfigTool` executable with SHA-256 `00c2d4053b40038836ec975c934958f64b986967faec7ecff682d88879103620`. The implementation surfaces are `beacon.adv_dynamic_data.DynamicData.setup_data`, `beacon.advset.AdvSet.add_payload_to_packet_ctl_tab`, `beacon.beacon_efuse_format.packetF1to7.toByteArray`, and `beacon.calibration.Calibration.adc_calibration_process`.

| Entry or option | What this build compiles |
| --- | --- |
| `<SPST-REG…>` | Memory trigger storage instead of the live register read. The full advertising config allocates snapshot storage by trigger set and register address. |
| `<QDEC 2byte 0 0>` | Register data at `0x1380`. The dynamic picker omits the defined Quadrature Decode Value item. The `qdec` settings block has `enable`, `runGpioEdgeDetect`, `clearCount`, `endCode`, `twoStep`, `interval`, `timeout`, `gpio`, and `code`. |
| `<AON-GPIO 1byte 0 0>` | GPIO status with the always-on selection bit set. The datasheet lists wakeup GPIO status as a source. [IN100 datasheet, §3.5.3](https://inplay-tech.com/IN100_datasheet.pdf#page=19). |
| `<PULSE 2byte 0 0>` | Alternate spelling for `<1-WIRE 2byte 0 0>`, using the configured pulse controller. |
| `<STRADDR 6byte 0 0>` | Six ASCII hexadecimal characters taken from the configured Bluetooth address. The compiler replaces the token with literal bytes. |
| `<RANDOM2 4byte 0 0>` | The picker exposes this as Static Random Number. It uses the random source with a different selector than `<RANDOM …>`. The picker and compiler support eight bytes for both random sources, while the v1.06 guide lists up to four bytes for Random Number. [InPlay Config Tool User Guide v1.06, §2.1.3](https://www.manualslib.com/manual/3441367/Inplay-Nanobeacon-In100.html?page=16). |
| `<VCC 2byte 0 0>` | `04 01` in place of `04 00` for one byte. Confirm the units and on-air output before using two-byte VCC. |
| `<REG2f80 8byte 0 0>` | Accepted by this build and emits an eight-byte field descriptor. v1.06 specifies up to four bytes for Register Read Data. Use SRAM and verify a capture when testing wider reads. [InPlay Config Tool User Guide v1.06, §2.1.3](https://www.manualslib.com/manual/3441367/Inplay-Nanobeacon-In100.html?page=16). |
| `<CTE 1byte 0 0>` | Accepted by the text validator and produces zero payload fields. Configure Constant Tone Extension through Advertising Parameters. [InPlay Config Tool User Guide v1.06, §2.1.6](https://www.manualslib.com/manual/3441367/Inplay-Nanobeacon-In100.html?page=26). |

## Advanced Settings in InPlay's documentation

The guide describes the Advanced application pane as a place for startup and runtime register overrides and points to InPlay support for register details. The separate Advanced Debug panel uses UART to access registers, memory and eFuse of a connected device. The IN100 stores executable configuration in different eFuse regions for global settings, register writes, advertising and I²C. The UART Host Controller API gives an attached MCU additional control, including changing the payload at runtime. [InPlay Config Tool User Guide v1.06, tool overview](https://www.manualslib.com/manual/3441367/Inplay-Nanobeacon-In100.html?page=11), [Advanced Settings](https://www.manualslib.com/manual/3441367/Inplay-Nanobeacon-In100.html?page=47), [IN100 datasheet, §§3.3, 4.1 and 4.2](https://inplay-tech.com/IN100_datasheet.pdf#page=16), [InPlay Host Controller API](https://github.com/NanoBeacon/config-files/tree/main/Host%20Controller%20API).

The cached-data application note adds examples for **cold boot**, **warm boot**, and **either**, with scheduling events such as wakeup, after ADC work and before sleep. The vendor note uses short labels `write:` and `delay:`. The installed tool's packet representation calls them `register write:` and `register delay:` and also represents a masked `register read-modify-write:`. A delay value is hexadecimal microseconds. The note's example `186A0` is 100 ms. The two copy-engine registers are `0x14C0` for copy control and `0x14C4` for source and destination. Cascading word copies through SRAM lets an advertisement include previous measurement values so a later packet can carry data from an earlier event. The copy moves words between addresses. [InPlay cached-data application note](https://github.com/NanoBeacon/config-files/tree/main/Store%20Cached%20Data).
