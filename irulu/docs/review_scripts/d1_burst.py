"""D1 independent burst check: cell EMF behind R, bulk C, event profile; exact piecewise-exponential solution."""
import math
def profile(i_tx, t_xo=0.8e-3, i_xo=1.5e-3, n_ch=3, t_tx=0.5e-3, t_gap=0.15e-3, i_gap=3e-3):
    seg = [(t_xo, i_xo)]
    for k in range(n_ch):
        seg.append((t_tx, i_tx))
        if k < n_ch-1 or True:
            seg.append((t_gap, i_gap))
    return seg
def vmin(voc, r, c, seg):
    v = voc; lo = v; q = 0
    for dur, i in seg:
        vinf = voc - i*r; tau = r*c
        v = vinf + (v - vinf)*math.exp(-dur/tau)   # monotone within a segment
        lo = min(lo, v); q += i*dur
    return lo, q
cases = [("fresh 20C", 1.55, 80), ("cold/half", 1.53, 150), ("EOL", 1.50, 250), ("cold EOL", 1.48, 400)]
print("charge per event, designer profile: 0 dBm %.1f uC, +4 dBm %.1f uC" % (vmin(1.55,80,88e-6,profile(9.1e-3))[1]*1e6, vmin(1.55,80,88e-6,profile(13.8e-3))[1]*1e6))
print("charge per event, slow-XO profile (1.0 ms XO at 2 mA, 0.6 ms TX): 0 dBm %.1f uC" % (vmin(1.55,80,88e-6,profile(9.1e-3,1.0e-3,2e-3,3,0.6e-3))[1]*1e6))
for itx, nm in ((9.1e-3, "0 dBm 9.1 mA"), (13.8e-3, "+4 dBm 13.8 mA")):
    print(f"\n{nm}: minimum VCC during one event (337-class cell R)")
    print("C_eff uF  " + "".join(f"{c[0]:>14s}" for c in cases))
    for C in (88, 80, 72, 60, 55, 45):
        print(f"{C:7d}   " + "".join(f"{vmin(v, r, C*1e-6, profile(itx))[0]:14.2f}" for _, v, r in cases))
print("\n377/364 cells (5-15 ohm @40 Hz per Energizer): 0 dBm, C=55 uF, R=15/40 ohm:",
      [round(vmin(1.55, r, 55e-6, profile(9.1e-3))[0],3) for r in (15, 40)])
# time for the cell to refill the capacitor after an event: tau = R*C
for r in (80,250,400):
    print(f"refill tau R={r} ohm, C=55 uF: {r*55e-6*1e3:.1f} ms")
# battery life
for cell, mah in (("337", 8.3), ("364/363", 23.0), ("377/376", 27.0)):
    for q in (13.3, 16.2):
        ia = 0.625e-6 + q*1e-6/3
        print(f"{cell:8s} Q={q:4.1f} uC @3 s: I_avg {ia*1e6:4.2f} uA -> {mah*1e-3/ia/24:5.0f} days to empty")
