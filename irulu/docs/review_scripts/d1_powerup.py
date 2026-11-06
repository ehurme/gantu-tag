"""D1 V1 power-up race: cell attached to an empty capacitor; CHIP_EN = VCC through 1k/100nF (follows VCC).
The IN100 is assumed to begin booting when VCC reaches V_START (internal POR, unpublished) and to run its first
advertising event after T_BOOT at I_BOOT. Reports the lowest VCC during that first event."""
import math
def first_event_min(voc, r, c, v_start, t_boot, i_boot=1.0e-3, i_tx=9.1e-3, dt=2e-6):
    seg = [(t_boot, i_boot), (0.8e-3, 1.5e-3)] + [(0.5e-3, i_tx), (0.15e-3, 3e-3)]*3
    v = 0.0; t = 0.0
    while v < v_start:                     # charge from empty, IN100 off (EN follows VCC, but below POR)
        v += (voc - v)/r/c*dt; t += dt
    lo = v; v_at_start = v
    for dur, i in seg:
        for _ in range(int(dur/dt)):
            v += ((voc - v)/r - i)/c*dt
            lo = min(lo, v)
    return lo
print("lowest VCC in the first advert after attaching the cell (V1, EN follows VCC); 0 dBm")
print("cell R  C_eff  " + "  ".join(f"Vstart{vs}/boot{tb*1e3:.0f}ms" for vs in (0.9, 1.1) for tb in (0.5e-3, 2e-3)))
for r in (10, 80, 150, 250):
    for c in (80e-6, 55e-6):
        print(f"{r:5d}  {c*1e6:4.0f}   " + "  ".join(f"{first_event_min(1.55, r, c, vs, tb):17.2f}" for vs in (0.9, 1.1) for tb in (0.5e-3, 2e-3)))
