"""D2 compact solar tag (v8.2): six photodiodes in series straight onto C1 -> IN100, with or without the start circuit.
Run: python3 tools/solar_sim.py   (writes nothing; README quotes docs/solar_sim.txt = this script's output)

Models (from datasheets unless marked ASSUMED):
  TEMD7000X01: Vo = 350 mV and Ik = 3 uA at Ee = 1 mW/cm2 (950 nm); TK(Vo) = -2.6 mV/K; TK(Ik) = +0.1 %/K.
    Daylight photocurrent: 1.5 uA per klx of sunlight at normal incidence (the independent review's ASTM G173 check
    gives 1.41-1.47; a white LED gives only ~0.5 uA/klx, halogen ~4). Diode law, ideality 1.2 (ASSUMED; 1.0/1.4 run).
    No blocking diode: the string sees the capacitor voltage directly, so the same diode law also gives the dark
    current back through the string when the light goes (I = Iph - I0 (exp(V / (N n Vt)) - 1), < 0 in the dark).
  C1 100 uF 0805 + C4 100 nF: 55 uF effective at ~1.5 V (independent review F1: Murata's model gives 72 uF at 0 V
    before DC bias; with bias, tolerance, cold and ageing ~55 uF typical, ~45 uF worst). v8.1 assumed 80-88 uF.
  S6 variants: U2 TPS3831G18: output high 200 ms after VCC passes VIT- + VHYS = 1.67 + 0.017 V, low when VCC < 1.67 V;
    150 nA typ (500 nA max run as a check). D2 RB751S40 drops 0.1 V into CHIP_EN and leaks ~50 nA back at 25 C
    (ASSUMED from the 30 V figure, x2 per 10 C) once U2 lets go. C5 330 nF holds CHIP_EN; R2 discharges it:
      S6  (v8.2 default): R2 3.3 Mohm, tau 1.1 s -> CHIP_EN well under 0.2 VCC by the second advert 3 s later, so
          the IN100 makes one advert per start unless the light keeps VCC above 1.67 V (then it runs on).
      S6L: R2 10 Mohm, tau 3.3 s (the v8.1 value) -> CHIP_EN ~0.45 VCC at 3 s, so whether a second advert happens
          depends on the IN100's unpublished CHIP_EN turn-off ratio K_OFF.
  IN100: turns on when CHIP_EN > 0.6 VCC (datasheet); once running, turns off when CHIP_EN < K_OFF x VCC (K_OFF is not
    published: 0.2 and 0.45 run). 16.2 uC per advertising event at 0 dBm on 3 channels (6.2 uC on one channel; 19 uC
    as a high case), 0.625 uA asleep, 10 nA off, 3 uC to boot (ASSUMED). The first advert follows the boot straight
    away (ASSUMED; the "after one interval" case is run too, review F6). VCC must stay >= 1.1 V while it runs; below
    that it must fall under 0.1 V before it restarts, so the sim counts the tag as STUCK (no more adverts in this run)
    if VCC drops under 1.1 V while it is on.
  N6: R1 1 Mohm from VCC with C5 330 nF (tau 0.33 s), no U2: CHIP_EN follows VCC, so the IN100 starts wherever its
    internal power-on reset lets go (V_POR, not in the datasheet: 1.0 / 1.3 / 1.5 V run).
"""
import math

VT0 = 0.025693
Q_ADV = 16.2e-6
Q_BOOT = 3.0e-6
I_SLEEP = 0.625e-6
I_OFF = 10e-9
I_SUP = 150e-9
C_EFF = 55.1e-6
C_H = 0.33e-6
R_PU = 1e6
VIT = 1.67
HYS = 0.017
T_DELAY = 0.2
VF_D2 = 0.10
I_D2_LEAK25 = 50e-9
K_ON = 0.6
INTERVAL = 3.0
V_BOR = 1.1
VMAX_ABS, VMAX_REC = 3.9, 3.6
UA_PER_KLX = 1.5e-6


def pd_i0(t_c, n):
    """Saturation current that gives the datasheet Vo = 350 mV at Ik = 3 uA (25 C), with TK(Vo) = -2.6 mV/K."""
    vt = VT0 * (t_c + 273.15) / 298.15
    voc_t = 0.350 - 2.6e-3 * (t_c - 25)
    return 3e-6 / (math.exp(voc_t / (n * vt)) - 1), vt


def string_current(vcap, n_pd, iph, t_c, n):
    """Current from the string into the capacitor (negative: the capacitor discharging back through it)."""
    i0, vt = pd_i0(t_c, n)
    return iph - i0 * (math.exp(min(vcap / (n_pd * n * vt), 80.0)) - 1)


def iph_of(klx, t_c, k=1.0):
    return k * UA_PER_KLX * klx * (1 + 0.001 * (t_c - 25))


def v_float(n_pd, klx, t_c, load=I_SUP, n=1.2):
    """Capacitor voltage where the string current falls to the standby load (IN100 off)."""
    iph = iph_of(klx, t_c)
    lo, hi = 0.0, 6.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if string_current(mid, n_pd, iph, t_c, n) > load:
            lo = mid
        else:
            hi = mid
    return lo


def run(klx, t_c=25, variant="S", r2=3.3e6, k_off=0.45, v_por=1.0, n=1.2, k=1.0, c=C_EFF, q_adv=Q_ADV,
        i_sup=I_SUP, first_delay=0.0, n_pd=6, t_end=600.0, dt=0.005):
    """Simulate t_end seconds from an empty capacitor. Returns dict(adverts/min, starts/min, min VCC while on,
    stuck flag, max VCC)."""
    iph = iph_of(klx, t_c, k)
    tbl_v = [i * 0.01 for i in range(0, 451)]   # 0 .. 4.5 V
    tbl_i = [string_current(x, n_pd, iph, t_c, n) for x in tbl_v]
    i_leak = I_D2_LEAK25 * 2 ** ((t_c - 25) / 10)

    def ich(x):
        j = min(max(int(x / 0.01), 0), 449)
        f = (x - tbl_v[j]) / 0.01
        return tbl_i[j] * (1 - f) + tbl_i[j + 1] * f

    v = en = t = 0.0
    sup_hi = False
    armed_at = None
    on = stuck = False
    next_adv = None
    adverts = starts = 0
    vmin_on, vmax = 9.9, 0.0
    while t < t_end:
        load = 0.0
        if variant == "S":
            if not sup_hi:
                if v >= VIT + HYS:
                    armed_at = t if armed_at is None else armed_at
                    if t - armed_at >= T_DELAY:
                        sup_hi = True
                else:
                    armed_at = None
            elif v < VIT:
                sup_hi, armed_at = False, None
            target = v - VF_D2
            if sup_hi:
                if en < target:
                    v -= (target - en) * C_H / c              # C5 charged from the store through U2 and D2
                en = target
                load += en / r2                               # U2 feeds R2 while it holds CHIP_EN
            else:
                en = max(0.0, en - (en / (r2 * C_H) + i_leak / C_H) * dt)
            load += i_sup
        else:
            en += (v - en) / (R_PU * C_H) * dt
        if not on and not stuck:
            enable = en > K_ON * v if variant == "S" else (en > K_ON * v and v >= v_por)
            if enable:
                on, starts = True, starts + 1
                v -= Q_BOOT / c
                next_adv = t + first_delay
        elif on and en < k_off * v:
            on = False
        if on:
            load += I_SLEEP
            if t >= next_adv:
                v -= q_adv / c
                adverts += 1
                next_adv = t + INTERVAL
            vmin_on = min(vmin_on, v)
            if v < V_BOR:
                stuck, on = True, False
        else:
            load += I_OFF
        v += (ich(min(max(v, 0.0), 4.49)) - load) * dt / c
        v = max(v, 0.0)
        vmax = max(vmax, v)
        t += dt
    return dict(apm=adverts / (t_end / 60), spm=starts / (t_end / 60), vmin=vmin_on if starts else None,
                stuck=stuck, vmax=vmax)


def fmt(r):
    s = f"{r['apm']:.1f}"
    if r["stuck"]:
        s += " STUCK"
    return s


def dark_drain(n_pd, v_from, v_to, t_c=25, n=1.2, c=C_EFF):
    """Seconds for the capacitor to fall from v_from to v_to through the dark string (IN100 off, U2 on)."""
    v, t, dt = v_from, 0.0, 0.05
    while v > v_to and t < 1e6:
        v += (string_current(v, n_pd, 0.0, t_c, n) - I_SUP - I_OFF) * dt / c
        t += dt
        dt = min(5.0, 0.002 * v / max(1e-15, -string_current(v, n_pd, 0.0, t_c, n) + I_SUP))
    return t


LUXES = [0.2, 0.5, 1, 2, 5, 10, 20, 100]


def table(title, rows):
    print(f"\n{title}")
    print(f"{'':34s}" + "".join(f"{l:>9g}klx" for l in LUXES))
    for name, kw in rows:
        res = [run(l, **kw) for l in LUXES]
        print(f"{name:34s}" + "".join(f"{fmt(r):>12s}" for r in res))


if __name__ == "__main__":
    print("Float voltage with the IN100 off (load 0.15 uA), V   [S6 start: 1.69 V; IN100 max 3.6 V recommended]")
    print("PDs T(C) " + "".join(f"{l:>7g}klx" for l in LUXES))
    for n_pd in (5, 6, 7):
        for t_c in (0, 25, 40):
            print(f"{n_pd}  {t_c:4d}  " + "".join(f"{v_float(n_pd, l, t_c):>10.2f}" for l in LUXES))

    print("\nAdverts per minute, 10 min from an empty capacitor (3 s interval: 20/min = running continuously).")
    print("STUCK = VCC fell under 1.1 V while the IN100 was on (brown-out lock until the store falls under 0.1 V).")
    base = [("S6  (R2 3.3M)", dict(r2=3.3e6)), ("S6L (R2 10M)", dict(r2=10e6))]
    table("25 C, C1 = 55 uF, 3 channels (16.2 uC), turn-off at 0.45 VCC",
          [(nm, dict(kw, k_off=0.45)) for nm, kw in base])
    table("25 C, C1 = 55 uF, 3 channels, turn-off at 0.2 VCC (the IN100 holds on to a lower CHIP_EN)",
          [(nm, dict(kw, k_off=0.2)) for nm, kw in base])
    table("25 C, worst case: C1 = 45 uF, 19 uC per advert, turn-off at 0.2 VCC",
          [(nm, dict(kw, k_off=0.2, c=45.1e-6, q_adv=19e-6)) for nm, kw in base])
    table("40 C, C1 = 55 uF, 3 channels (D2 leaks ~140 nA)",
          [(nm + f" k_off {ko}", dict(kw, t_c=40, k_off=ko)) for nm, kw in base for ko in (0.2, 0.45)])
    table("If the IN100 waits one interval before its first advert (review F6), 25 C, 55 uF",
          [(nm + f" k_off {ko}", dict(kw, k_off=ko, first_delay=INTERVAL)) for nm, kw in base for ko in (0.2, 0.45)])
    table("One advertising channel (6.2 uC per event; OTP setting), 25 C, 55 uF",
          [(nm + f" k_off {ko}", dict(kw, k_off=ko, q_adv=6.2e-6)) for nm, kw in base for ko in (0.2, 0.45)])
    table("TPS3831 at its 500 nA maximum, 25 C, 55 uF, k_off 0.45",
          [(nm, dict(kw, i_sup=500e-9)) for nm, kw in base])
    table("S6 (3.3M), 25 C, 55 uF: daylight factor 0.7 / 1.3 and diode ideality 1.0 / 1.4",
          [(f"n={n} k={k}", dict(n=n, k=k)) for n, k in ((1.2, 0.7), (1.2, 1.3), (1.0, 1.0), (1.4, 1.0))])
    table("N6 (no start circuit), 25 C, 55 uF, three guesses of the IN100's power-on reset level",
          [(f"V_POR {vp} V", dict(variant="N", v_por=vp)) for vp in (1.0, 1.3, 1.5)])

    print("\nHighest capacitor voltage, full sun 100 klx, IN100 off (ideality 1.2 / 1.0):")
    for t_c in (25, 0, -10):
        print(f"6 PDs at {t_c:3d} C: {v_float(6, 100, t_c):.2f} V / {v_float(6, 100, t_c, n=1.0):.2f} V "
              f"(IN100 recommended max {VMAX_REC} V, abs max {VMAX_ABS} V; on-chip VCC ADC only to 3.0 V)")

    print("\nNo blocking diode: dark current back through the string (25 C), and time to drain C1 in the dark")
    for vc in (1.1, 1.69, 2.0, 2.5, 3.0):
        print(f"  at {vc:.2f} V: {-string_current(vc, 6, 0.0, 25, 1.2) * 1e6:8.3f} uA")
    print(f"  {2.5:.1f} V -> 1.69 V: {dark_drain(6, 2.5, 1.69):6.0f} s;  1.69 V -> 1.1 V: {dark_drain(6, 1.69, 1.1):6.0f} s")
    i_prog = -string_current(3.3, 6, 0.0, 25, 1.0)
    print(f"  programmer at 3.3 V into the dark string: {i_prog * 1e3:.1f} mA (ideality 1.0, worst case), on top of "
          f"up to 50 mA for OTP programming")
    for c in (55.1e-6, 45.1e-6):
        q_hold = c * (VIT + HYS - V_BOR)
        print(f"\nC1 = {c * 1e6:.0f} uF: charge between start (1.69 V) and the 1.1 V floor {q_hold * 1e6:.0f} uC = "
              f"{(q_hold - Q_BOOT) / Q_ADV:.1f} adverts after boot (no light); one advert takes VCC from 1.69 V to "
              f"{VIT + HYS - (Q_BOOT + Q_ADV) / c:.2f} V")
