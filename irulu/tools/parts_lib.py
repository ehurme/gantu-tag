"""Shared part definitions for the v8 designs: custom symbols and the JLC part data checked on 2 Nov 2026.

Each entry of PARTDB: (value, LCSC, MPN, manufacturer, footprint, symbol, library type, stock on 2 Nov 2026).
"""

LIB = "insect_tag"

PARTDB = {
    "IN100":    ("IN100-Q1-R-RC1I", "C6062024", "IN100-Q1-R-RC1I", "InPlay", "InPlay_IN100_QFN-18-1EP_3x3mm_P0.4mm_EP1.5x1.7mm", "IN100_QFN18", "Ext", 753),
    "XTAL":     ("26MHz 7pF", "C5203638", "8Q26000008", "TXC", "Crystal_SMD_1612-4Pin_1.6x1.2mm", "Device:Crystal_GND24", "Ext", 1313),
    "C100U":    ("100uF 6.3V X5R", "C141660", "GRM21BR60J107ME15L", "Murata", "C_0805_2012Metric", "Device:C", "Ext", 27104),
    "C10U":     ("10uF 6.3V X5R", "C15525", "CL05A106MQ5NUNC", "Samsung", "C_0402_1005Metric", "Device:C", "Basic", 10099327),
    "C100N":    ("100nF", "C1525", "CL05B104KO5NNNC", "Samsung", "C_0402_1005Metric", "Device:C", "Basic", 36039359),
    "C10N":     ("10nF", "C15195", "CL05B103KB5NNNC", "Samsung", "C_0402_1005Metric", "Device:C", "Basic", 6130952),
    "C1N":      ("1nF", "C1523", "0402B102K500NT", "FH", "C_0402_1005Metric", "Device:C", "Basic", 2423042),
    "C1U":      ("1uF", "C52923", "CL05A105KA5NQNC", "Samsung", "C_0402_1005Metric", "Device:C", "Basic", 0),
    "C220N":    ("220nF", "C16772", "CL05B224KO5NNNC", "Samsung", "C_0402_1005Metric", "Device:C", "Basic", 1314294),
    "R1K":      ("1k", "C11702", "0402WGF1001TCE", "UNI-ROYAL", "R_0402_1005Metric", "Device:R", "Basic", 21629345),
    "R100K":    ("100k", "C25741", "0402WGF1003TCE", "UNI-ROYAL", "R_0402_1005Metric", "Device:R", "Basic", 0),
    "R1M":      ("1M", "C26083", "0402WGF1004TCE", "UNI-ROYAL", "R_0402_1005Metric", "Device:R", "Basic", 2929984),
    "R10M":     ("10M", "C26082", "0402WGF1005TCE", "UNI-ROYAL", "R_0402_1005Metric", "Device:R", "Preferred", 68300),
    "R3M3":     ("3.3M", "C270613", "0402WGF3304TCE", "UNI-ROYAL", "R_0402_1005Metric", "Device:R", "Ext", 19910),
    "R0":       ("0R", "C17168", "0402WGF0000TCE", "UNI-ROYAL", "R_0402_1005Metric", "Device:R", "Basic", 11244920),
    "R4K7":     ("4.7k", "C25900", "0402WGF4701TCE", "UNI-ROYAL", "R_0402_1005Metric", "Device:R", "Basic", 14846048),
    "R10":      ("10R", "C25077", "0402WGF100JTCE", "UNI-ROYAL", "R_0402_1005Metric", "Device:R", "Basic", 3187946),
    "PD":       ("TEMD7000X01", "C145328", "TEMD7000X01", "Vishay", "PD_0805_TEMD7000", "Device:D_Photo", "Ext", 2559),
    "SCHOTTKY": ("RB751S40T1G", "C232576", "RB751S40T1G", "onsemi", "D_SOD-523", "Device:D_Schottky", "Ext", 46366),
    "SUP_START": ("TPS3839G25DBZR", "C702201", "TPS3839G25DBZR", "Texas Instruments", "SOT-23-3", "TPS3839DBZ", "Ext", 716),
    "SUP_STOP": ("TPS3839G18DBZR", "C544505", "TPS3839G18DBZR", "Texas Instruments", "SOT-23-3", "TPS3839DBZ", "Ext", 3041),
    "SUP_X2SON": ("TPS3831G18DQNR", "C2066667", "TPS3831G18DQNR", "Texas Instruments", "Texas_X2SON-4_1x1mm_P0.65mm", "TPS3831DQN", "Ext", 52),
    "C330N":    ("330nF 10V X5R", "C107013", "CC0402KRX5R6BB334", "YAGEO", "C_0402_1005Metric", "Device:C", "Ext", 173178),
    "MOSPAIR":  ("Si1553CDL", "C467894", "SI1553CDL-T1-GE3", "Vishay", "SOT-363_SC-70-6", "Si1553CDL", "Ext", 11910),
    "IMU":      ("LSM303AGR", "C126671", "LSM303AGRTR", "STMicroelectronics", "LGA-12_2x2mm_P0.5mm", "LSM303AGR", "Ext", 2231),
    "BARO":     ("BMP581", "C5362283", "BMP581", "Bosch Sensortec", "Bosch_LGA-10_2x2mm_P0.5mm_BMP581", "BMP581", "Ext", 7242),
    "XIAO":     ("XIAO nRF52840", "C17209540", "102010448", "Seeed", "Seeed_XIAO_nRF52840_SMD", "XIAO_nRF52840_SMD", "Ext", 48),
}


def part(key, ref, pcb, sch, **kw):
    v, lcsc, mpn, mfr, fp, sym, _, _ = PARTDB[key]
    d = dict(ref=ref, value=kw.pop("value", v), fp=f"{LIB}:{fp}", sym=sym if ":" in sym else f"{LIB}:{sym}",
             fields={"LCSC": lcsc, "MPN": mpn, "Manufacturer": mfr}, pcb=pcb, sch=sch)
    note = kw.pop("note", None)
    if note:
        d["fields"]["Note"] = note
    d.update(kw)
    return d


def variant_value(key):
    v, lcsc, mpn, mfr = PARTDB[key][:4]
    return (v, lcsc, mpn, mfr)


# ---------------------------------------------------------------- custom symbols (pins: number, name, side, type)
IN100_PINS = [("18", "CHIP_EN", "L", "in"), ("1", "XO_N", "L", "pas"), ("2", "XO_P", "L", "pas"),
              ("8", "GPIO0/RXD", "L", "bidi"), ("9", "GPIO1/TXD", "L", "bidi"), ("12", "MGPIO4", "L", "bidi"),
              ("5", "MGPIO5", "L", "bidi"), ("4", "MGPIO6", "L", "bidi"), ("3", "MGPIO7", "L", "bidi"),
              ("17", "VCC", "R", "pwr"), ("13", "VDDQ", "R", "pwr"), ("16", "RF_TX", "R", "pas"),
              ("14", "RTC_XO_P", "R", "pas"), ("15", "RTC_XO_N", "R", "pas"), ("10", "GPIO2", "R", "bidi"),
              ("11", "GPIO3", "R", "bidi"), ("6", "SW0", "R", "pas"), ("7", "SW1", "R", "pas"),
              ("19", "GND/EP", "B", "pwr")]

SYMBOLS_ALL = {
    "IN100_QFN18": dict(value="IN100-Q1-R-RC1I", footprint=f"{LIB}:InPlay_IN100_QFN-18-1EP_3x3mm_P0.4mm_EP1.5x1.7mm",
                        descr="InPlay IN100 NanoBeacon BLE beacon SoC, QFN18 3x3mm, 1.1-3.6V",
                        keywords="BLE beacon NanoBeacon InPlay", pins=IN100_PINS, width=27.94),
    "TPS3839DBZ": dict(value="TPS3839", footprint=f"{LIB}:SOT-23-3", descr="Nanopower supervisor, push-pull active-low RESET",
                       keywords="supervisor reset", pins=[("3", "VDD", "L", "pwr"), ("1", "GND", "B", "pwr"),
                                                          ("2", "~{RESET}", "R", "out")], width=17.78),
    "TPS3831DQN": dict(value="TPS3831", footprint=f"{LIB}:Texas_X2SON-4_1x1mm_P0.65mm",
                       descr="Nanopower supervisor, push-pull active-low RESET, manual reset input (internal pull-up)",
                       keywords="supervisor reset", pins=[("4", "VDD", "L", "pwr"), ("2", "~{MR}", "L", "in"),
                                                          ("3", "GND", "B", "pwr"), ("5", "EP", "B", "pwr"),
                                                          ("1", "~{RESET}", "R", "out")], width=17.78),
    "Si1553CDL": dict(value="Si1553CDL", footprint=f"{LIB}:SOT-363_SC-70-6", ref="Q",
                      descr="Complementary N + P MOSFET pair, SC-70-6 (1 S1 2 G1 6 D1 = N; 4 S2 5 G2 3 D2 = P)",
                      keywords="mosfet complementary", pins=[("2", "G1(N)", "L", "pas"), ("1", "S1(N)", "L", "pas"),
                                                            ("6", "D1(N)", "L", "pas"), ("5", "G2(P)", "R", "pas"),
                                                            ("4", "S2(P)", "R", "pas"), ("3", "D2(P)", "R", "pas")],
                      width=17.78),
    "LSM303AGR": dict(value="LSM303AGR", footprint=f"{LIB}:LGA-12_2x2mm_P0.5mm",
                      descr="ST LSM303AGR 3-axis accelerometer + 3-axis magnetometer, I2C/SPI, LGA-12",
                      keywords="accelerometer magnetometer compass",
                      pins=[("9", "Vdd", "L", "pwr"), ("10", "Vdd_IO", "L", "pwr"), ("2", "CS_XL", "L", "in"),
                            ("3", "CS_MAG", "L", "in"), ("5", "C1", "L", "pas"), ("1", "SCL/SPC", "R", "in"),
                            ("4", "SDA/SDI/SDO", "R", "bidi"), ("12", "INT_1_XL", "R", "out"),
                            ("11", "INT_2_XL", "R", "out"), ("7", "INT_MAG/DRDY", "R", "out"),
                            ("6", "GND", "B", "pwr"), ("8", "GND", "B", "pwr")], width=22.86),
    "BMP581": dict(value="BMP581", footprint=f"{LIB}:Bosch_LGA-10_2x2mm_P0.5mm_BMP581",
                   descr="Bosch BMP581 barometric pressure sensor, I2C/SPI/I3C, LGA-10 2x2mm",
                   keywords="pressure barometer altitude",
                   pins=[("10", "VDD", "L", "pwr"), ("1", "VDDIO", "L", "pwr"), ("6", "CSB", "L", "in"),
                         ("5", "SDO", "L", "bidi"), ("2", "SCK", "R", "in"), ("4", "SDI", "R", "bidi"),
                         ("7", "INT", "R", "out"), ("3", "VSS", "B", "pwr"), ("8", "VSS", "B", "pwr"),
                         ("9", "VSS", "B", "pwr")], width=17.78),
    "XIAO_nRF52840_SMD": dict(value="XIAO nRF52840", footprint=f"{LIB}:Seeed_XIAO_nRF52840_SMD", ref="M",
                              descr="Seeed Studio XIAO nRF52840, SMD castellated with bottom pads",
                              keywords="nRF52840 BLE module Seeed XIAO",
                              pins=[("1", "D0", "L", "bidi"), ("2", "D1", "L", "bidi"), ("3", "D2", "L", "bidi"),
                                    ("4", "D3", "L", "bidi"), ("5", "D4/SDA", "L", "bidi"), ("6", "D5/SCL", "L", "bidi"),
                                    ("7", "D6/TX", "L", "bidi"), ("8", "D7/RX", "L", "bidi"), ("9", "D8", "L", "bidi"),
                                    ("10", "D9", "L", "bidi"), ("11", "D10", "L", "bidi"),
                                    ("14", "VBUS", "R", "pas"), ("12", "3V3", "R", "pout"), ("19", "VBAT", "R", "pas"),
                                    ("13", "GND", "R", "pwr"), ("18", "GND", "R", "pwr"), ("20", "GND", "R", "pwr"),
                                    ("15", "SWDIO", "R", "bidi"), ("16", "SWCLK", "R", "in"), ("17", "RST", "R", "in"),
                                    ("21", "NFC1", "R", "pas"), ("22", "NFC2", "R", "pas")], width=22.86),
}
