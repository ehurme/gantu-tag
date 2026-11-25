"""How many adverts Hagalu's light can pay for, and where to gate a second network.
Run: python3 tools/advert_budget.py   (writes nothing; docs/advert_budget.txt is this script's output)

Uses solar_sim.py's photodiode string (six TEMD7000X01, ideality 1.2) and C1's 55 uF effective capacitance, and
calibrates the rest against measurements:

  Lamp ramp, 22 Nov 2026 (pi-bench.md): median gaps while each tag restarted for every advert, white LED, phone lux.
    Hagalu-003 (S6L, 0 dBm): 2.07 / 4.34 / 11.08 / 30.58 / ~125 s at 23.6 / 12.2 / 6.0 / 3.0 / 1.59 klx
    Hagalu-004 (S6L, +4 dBm): 2.11 / 5.32 / 14.43 / 37.77 / ~104 s
    The fit uses the middle three steps. At 23.6 klx both tags sat at ~2.1 s whatever their power, which looks like
    S6L's CHIP_EN hold rather than the light; the 1.59 klx gaps rest on two and five adverts.
  Balcony, 24-25 Nov 2026: fastest restarts 0.6-0.7 s on S6 (Hagalu-006) and 1.1-1.7 s on S6L (Hagalu-004);
    all three tags stayed on at their set intervals in steady afternoon sun on 25 Nov.

Model of one restart: the supervisor starts the IN100 at 1.687 V; boot plus one advert take Q_cycle out of C1;
the string recharges C1 back to 1.687 V; the supervisor waits 200 ms. Gap = recharge time + 0.2 s. While the tag
stays on, each advert takes Q_adv and C1 runs a sawtooth whose trough must stay above U2's 1.67 V, or U2 drops
CHIP_EN and the tag falls back to restarting.

ASSUMED: a white LED gives 1/3 of daylight's photocurrent per lux (solar_sim.py's 0.5 vs 1.5 uA/klx); the lamp ran
at 20 C; Q_adv = Q_cycle - 4.5 uC (boot 3 uC, C5 0.5 uC, standby during the CHIP_EN hold ~1 uC); 1.2 uA of standby
load while on (IN100 asleep 0.625 uA, U2 0.15 uA, R2). The LED factor and Q_cycle trade off against each other:
the lamp fixes only their ratio, so a second calibration (LED = 1/4) is printed as a check.
"""
import math

import solar_sim as S

V_ON = S.VIT + S.HYS          # 1.687 V: U2 releases CHIP_EN (after 200 ms)
V_OFF = S.VIT                 # 1.67 V: U2 drops CHIP_EN
C = S.C_EFF
I_STATIC = 1.2e-6
OVERHEAD = 4.5e-6
LED = 1 / 3

LAMP = [12.2, 6.0, 3.0]
GAPS = {"Hagalu-003 (0 dBm)": [4.34, 11.08, 30.58],
        "Hagalu-004 (+4 dBm)": [5.32, 14.43, 37.77]}


def i_net(v, klx, t_c, load=I_STATIC):
    i0, vt = S.pd_i0(t_c, 1.2)
    return S.iph_of(klx, t_c) - i0 * (math.exp(min(v / (6 * 1.2 * vt), 80.0)) - 1) - load


def t_charge(v0, v1, klx, t_c, c=C, load=I_STATIC, steps=200):
    """Seconds for the string to lift C1 from v0 to v1 against a steady load (inf if it can't)."""
    h, t = (v1 - v0) / steps, 0.0
    for j in range(steps):
        i = i_net(v0 + (j + 0.5) * h, klx, t_c, load)
        if i <= 0:
            return math.inf
        t += c * h / i
    return t


def restart_gap(q_cycle, klx, t_c=20, c=C):
    return t_charge(V_ON - q_cycle / c, V_ON, klx, t_c, c, load=0.3e-6) + 0.2


def fit_q(gaps, k, t_c=20):
    best = None
    for q10 in range(80, 800):
        q = q10 * 0.1e-6
        e = sum(math.log(restart_gap(q, k * lx, t_c) / g) ** 2 for lx, g in zip(LAMP, gaps))
        if best is None or e < best[0]:
            best = (e, q)
    return best[1], math.sqrt(best[0] / len(gaps))


def peak_for_interval(T, q, klx, t_c, c=C):
    """Peak VCC of the steady sawtooth at interval T (None if the light can't pay for it)."""
    dv = q / c
    lo, hi = V_OFF - 0.6, 3.6
    if t_charge(hi - dv, hi, klx, t_c, c) < T:
        return hi
    if t_charge(lo, lo + dv, klx, t_c, c) > T:
        return None
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if t_charge(mid, mid + dv, klx, t_c, c) < T:
            lo = mid
        else:
            hi = mid
    return lo + dv


def fastest_on(q, klx, t_c, c=C, v_floor=V_OFF):
    """Shortest interval that keeps the trough above v_floor: the light's whole budget, spent on one network."""
    return t_charge(v_floor, v_floor + q / c, klx, t_c, c)


def fall_time(v_from, v_to, load, t_c=25, c=C):
    """Seconds for VCC to fall from v_from to v_to in the dark under an average load."""
    h, t = (v_from - v_to) / 100, 0.0
    for j in range(100):
        i = -i_net(v_from - (j + 0.5) * h, 0.0, t_c, load)
        t += c * h / i
    return t


DAY = [2, 5, 10, 20, 40, 100]

if __name__ == "__main__":
    print("1. Calibration: restart gaps under the lamp, model vs measured (s)")
    q_fit = {}
    for k_name, k in (("LED = 1/3 daylight (solar_sim)", LED), ("LED = 1/4 daylight (check)", 0.25)):
        print(f"   {k_name}")
        for name, gaps in GAPS.items():
            q, rms = fit_q(gaps, k)
            q_fit[(k, name)] = q
            pred = " ".join(f"{restart_gap(q, k * lx):6.1f}" for lx in LAMP)
            meas = " ".join(f"{g:6.1f}" for g in gaps)
            print(f"     {name:20s} Q_cycle {q * 1e6:4.1f} uC (rms log error {rms:.2f})  model {pred}  measured {meas}")
    q0c, q4c = q_fit[(LED, "Hagalu-003 (0 dBm)")], q_fit[(LED, "Hagalu-004 (+4 dBm)")]
    Q0, Q4 = q0c - OVERHEAD, q4c - OVERHEAD
    print(f"   +4 dBm costs {100 * (q4c / q0c - 1):.0f}% more per start under either calibration.")
    print(f"   Used below: Q_adv {Q0 * 1e6:.1f} uC at 0 dBm, {Q4 * 1e6:.1f} uC at +4 dBm (3 channels); one advert drops "
          f"VCC by {Q0 / C:.2f} / {Q4 / C:.2f} V on {C * 1e6:.0f} uF.")

    print("\n2. Restart regime (one advert per start): gap and adverts/s by daylight, 25 C")
    print("   klx            " + "".join(f"{d:>8g}" for d in DAY))
    for name, q in (("0 dBm", q0c), ("+4 dBm", q4c)):
        g = [restart_gap(q, d, 25) for d in DAY]
        print(f"   {name:7s} gap s  " + "".join(f"{x:8.2f}" for x in g))
    print("   Hold floor: S6 can't restart faster than ~0.6-0.7 s, S6L ~1.1-1.7 s (balcony minima).")

    print("\n3. Staying on: fastest interval the light pays for with the trough above 1.67 V (s), and adverts/s")
    for t_c in (25, 40):
        print(f"   {t_c} C     klx  " + "".join(f"{d:>8g}" for d in DAY))
        for name, q in (("0 dBm", Q0), ("+4 dBm", Q4)):
            t = [fastest_on(q, d, t_c) for d in DAY]
            print(f"   {name:7s} T_min  " + "".join(f"{x:8.2f}" if x < 99 else f"{'-':>8s}" for x in t))
            print(f"   {'':7s} adv/s  " + "".join(f"{1 / x:8.2f}" if x < 99 else f"{'-':>8s}" for x in t))

    print("\n4. Peak VCC while on (the gate reads about this), Find My only, +4 dBm")
    for t_c in (25, 40):
        print(f"   {t_c} C     klx  " + "".join(f"{d:>8g}" for d in DAY))
        for T in (1, 2, 3):
            p = [peak_for_interval(T, Q4, d, t_c) for d in DAY]
            print(f"   T = {T} s        " + "".join(f"{x:8.2f}" if x and x - Q4 / C >= V_OFF else f"{'off':>8s}"
                                                  for x in p))

    print("\n5. Gate for a second network. A restart is harmless; a lock needs VCC under 1.1 V with CHIP_EN held.")
    print("   V_gate keeps the tag on through a Hubble advert (trough >= 1.67 V) and clear of the lock through a")
    print("   Hubble and a Find My advert back to back (>= 1.1 V), with 0.05 V margin. Both +4 dBm.")
    for c in (45e-6, 55e-6, 72e-6, 100e-6):
        on = V_OFF + Q4 / c + 0.05
        lock = S.V_BOR + 2 * Q4 / c + 0.05
        print(f"   C1 effective {c * 1e6:3.0f} uF: {max(on, lock):.2f} V  (stay on {on:.2f}, no lock {lock:.2f})")
    vg = round(max(V_OFF + Q4 / C, S.V_BOR + 2 * Q4 / C) + 0.05, 2)

    print(f"\n6. With the gate at {vg:.2f} V: lowest daylight (klx) at which Find My alone lifts the peak past it")
    for t_c in (25, 40):
        row = []
        for Tf in (1, 1.5, 2, 3):
            d = next((x for x in [2 + 0.5 * j for j in range(400)]
                      if (peak_for_interval(Tf, Q4, x, t_c) or 0) >= vg
                      and peak_for_interval(Tf, Q4, x, t_c) - Q4 / C >= V_OFF), None)
            row.append(f"Find My {Tf:g} s: {d:5.1f}" if d else f"Find My {Tf:g} s:   >200")
        print(f"   {t_c} C   " + "   ".join(row))

    print(f"\n7. Hubble interval the spare light pays for while VCC is held at {vg:.2f} V (s; '-' = gate stays shut)")
    for t_c in (25, 40):
        print(f"   {t_c} C           klx  " + "".join(f"{d:>8g}" for d in DAY))
        for Tf in (1, 1.5, 2, 3):
            row = []
            for d in DAY:
                spare = i_net(vg, d, t_c) - Q4 / Tf
                row.append(f"{Q4 / spare:8.1f}" if spare > 0 else f"{'-':>8s}")
            print(f"   Find My T = {Tf:<3g} s    " + "".join(row))

    print(f"\n8. Falloff when the light goes: seconds from {vg:.2f} V to 1.67 V in the dark (+4 dBm Find My)")
    for Tf in (1, 2, 3, 6):
        print(f"   Find My T = {Tf} s: {fall_time(vg, V_OFF, Q4 / Tf + I_STATIC):5.1f} s")
