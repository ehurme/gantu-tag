"""D2 static checks: 6 x TEMD7000X01 in series straight onto VCC (no blocking diode)."""
import math
VT0 = 0.025693
def vt(tc): return VT0*(tc+273.15)/298.15
def vo(tc): return 0.350 - 2.6e-3*(tc-25)          # Vo at Ik = 3 uA (Ee 1 mW/cm2, 950 nm), datasheet
def i0(tc, n): return 3e-6*(1+0.001*(tc-25))/(math.exp(vo(tc)/(n*vt(tc)))-1)
def idiode(v, tc, n): return i0(tc, n)*(math.exp(v/(n*vt(tc)))-1)   # forward (dark) current of one PD at v
def iph(klx, tc, k=1.45e-6): return k*klx*(1+0.001*(tc-25))
def vstring(i_load, klx, tc, n, N=6):
    ip = iph(klx, tc)
    if ip <= i_load: return 0.0
    return N*n*vt(tc)*math.log((ip-i_load)/i0(tc, n)+1)
print("Open-circuit voltage of 6 PDs (no load), 1.45 uA/klx sun, V")
print("  T   n    " + "".join(f"{l:>8g}klx" for l in (0.5,1,5,20,100)))
for tc in (25, 40, 0, -10):
    for n in (1.0, 1.2, 1.5, 2.0):
        print(f"{tc:4d} {n:3.1f}  " + "".join(f"{vstring(0, l, tc, n):11.2f}" for l in (0.5,1,5,20,100)))
print("\nMax VCC full sun, IN100 asleep (load ~1 uA):")
for tc in (0, -10, -20):
    for klx in (100, 120):
        print(f"  {tc:4d} C {klx} klx: " + "  ".join(f"n={n}: {vstring(1e-6, klx, tc, n):.2f} V" for n in (1.0, 1.2, 1.5, 2.0)))
print("\nLight needed to lift VCC to the TPS3831 release point (VIT+ = 1.687 V typ; 1.712 V max) against a standby load")
for vrel in (1.687, 1.712):
    for load in (0.16e-6, 0.5e-6):
        for tc in (25, 40):
            out = []
            for n in (1.0, 1.2, 1.5):
                # solve iph - load = idiode(vrel/6)
                need = load + idiode(vrel/6, tc, n)
                out.append(f"n={n}: {need/1.45e-6*(1/(1+0.001*(tc-25))):.2f} klx")
            print(f"  Vrel {vrel} V, load {load*1e9:.0f} nA, {tc} C: " + "  ".join(out))
print("\nDark forward current of the string (one PD at V/6) -> drains the store in the dark / loads the programmer")
for V in (1.0, 1.3, 1.5, 1.7, 2.0, 2.5, 3.0, 3.3, 3.6):
    print(f"  VCC {V:3.1f} V ({V/6:.3f} V/PD): " + "  ".join(f"n={n}: {idiode(V/6, 25, n)*1e6:9.3f} uA" for n in (1.0, 1.2, 1.5, 2.0))
          + f"   | 40C n=1.2: {idiode(V/6, 40, 1.2)*1e6:.3f} uA")
# empirical bound from VF = 1 V at 50 mA (datasheet) : log-linear between (0.35 V, 3 uA) and (1.0 V, 50 mA)
s = (1.0-0.35)/math.log(50e-3/3e-6)
print(f"  log-linear bound through (0.35 V,3 uA)-(1.0 V,50 mA): n_eff*Vt = {s*1e3:.1f} mV -> at 3.3 V: {3e-6*math.exp((0.55-0.35)/s)*1e6:.0f} uA")
