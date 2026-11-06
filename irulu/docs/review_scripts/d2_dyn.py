"""D2 S6 / N6 dynamic check (independent re-implementation, derived from the designer's solar_sim.py structure).
6 x TEMD7000X01 straight onto VCC (no blocking diode). Parameters swept: C_eff, charge per advert, IN100 turn-off
ratio K_OFF (CHIP_EN/VCC below which the running IN100 shuts down; datasheet gives only VIH = 0.6 VCC), D2 reverse
leakage, TPS3831 IDD. STUCK = VCC fell below 1.1 V while CHIP_EN was still above K_OFF*VCC (datasheet: then it must
go below 0.1 V before it can restart)."""
import math, sys
VT0 = 0.025693
def vt(tc): return VT0*(tc+273.15)/298.15
def i0(tc, n): return 3e-6*(1+0.001*(tc-25))/(math.exp((0.350-2.6e-3*(tc-25))/(n*vt(tc)))-1)
def i_string(v, iph, tc, n, N=6):
    return iph - i0(tc, n)*(math.exp(max(v, -0.5)/N/(n*vt(tc)))-1)   # can go negative (dark discharge)

def run(klx, tc=25, C=55e-6, Qadv=16.2e-6, Qboot=3e-6, k_off=0.45, n=1.2, kday=1.45e-6, variant="S",
        i_sup=150e-9, d2_leak=60e-9, vit=1.67, hys=0.017, tdel=0.2, R2=10e6, C5=0.33e-6, R1=1e6,
        interval=3.0, t_end=600.0, dt=0.002, v_por=1.0, first_advert_delay=0.0):
    iph = kday*klx*(1+0.001*(tc-25))
    v = en = t = 0.0; sup = False; armed = None; on = stuck = False; nxt = None
    adv = starts = 0; vmin_on = 9.9; vmax = 0
    while t < t_end:
        load = 0.0
        if variant == "S":
            if not sup:
                if v >= vit+hys:
                    armed = t if armed is None else armed
                    if t-armed >= tdel: sup = True
                else: armed = None
            elif v < vit: sup, armed = False, None
            tgt = v - 0.12                                   # RB751 at ~uA
            if sup and en < tgt:
                v -= (tgt-en)*C5/C; en = tgt
            else:
                # R2 plus D2 reverse leakage (Schottky, ~voltage-independent at 1-2 V) when U2 output is low
                i_dis = en/R2 + (0 if sup else d2_leak*min(1.0, en/0.5))
                en = max(0.0, en - i_dis/C5*dt)
            load += i_sup + en/R2
        else:   # N: R1 from VCC to CHIP_EN, C5 to GND
            en += (v-en)/(R1*C5)*dt
        if not on and not stuck:
            ok = en > 0.6*v and (variant == "S" or v >= v_por)
            if ok:
                on = True; starts += 1; v -= Qboot/C; nxt = t + first_advert_delay
        elif on and en < k_off*v:
            on = False
        if on:
            load += 0.625e-6
            if t >= nxt:
                v -= Qadv/C; adv += 1; nxt = t + interval
            vmin_on = min(vmin_on, v)
            if v < 1.1: stuck, on = True, False
        else:
            load += 10e-9
        v += (i_string(v, iph, tc, n) - load)*dt/C
        v = max(v, 0.0); vmax = max(vmax, v); t += dt
    return adv/(t_end/60), starts/(t_end/60), (vmin_on if starts else None), stuck

def fmt(r):
    a, s, vm, st = r
    return ("STUCK" if st else f"{a:4.1f}") + ("" if vm is None else f"/{vm:.2f}")
lux = [0.3, 0.5, 1, 2, 5, 10, 20, 100]
print("cells: adverts per min / lowest VCC while running (STUCK = brown-out lock); 10 min from empty; 0 dBm unless noted")
print(" " * 44 + "".join(f"{l:>11g}k" for l in lux))
def row(label, **kw):
    print(f"{label:44s}" + "".join(f"{fmt(run(l, **kw)):>12s}" for l in lux)); sys.stdout.flush()
row("S6 designer-like: C88 Q16.2 koff.45 25C", C=88e-6, d2_leak=0)
row("S6 C80 (no C3) Q16.2 koff.45 25C", C=80e-6, d2_leak=0)
row("S6 C55 Q16.2 koff.45 25C", C=55e-6)
row("S6 C55 Q16.2 koff.30 25C", C=55e-6, k_off=0.30)
row("S6 C55 Q16.2 koff.20 25C", C=55e-6, k_off=0.20)
row("S6 C45 Q19 koff.30 25C", C=45e-6, Qadv=19e-6, k_off=0.30)
row("S6 C55 Q13.3 koff.45 25C", C=55e-6, Qadv=13.3e-6)
row("S6 C55 Q16.2 koff.45 40C leak200n", C=55e-6, tc=40, d2_leak=200e-9)
row("S6 C55 +4dBm Q23.3 koff.45 25C", C=55e-6, Qadv=23.3e-6)
row("S6 C55 +4dBm Q23.3 koff.30 25C", C=55e-6, Qadv=23.3e-6, k_off=0.30)
row("S6 C55 Q16.2 koff.45 first advert after 1 interval", C=55e-6, first_advert_delay=3.0)
row("S6 C55 Q16.2 koff.45 Iq 500nA", C=55e-6, i_sup=500e-9)
for vp in (1.0, 1.3, 1.5):
    row(f"N6 C55 Q16.2 V_POR {vp}", C=55e-6, variant="N", v_por=vp)
