import sys
sys.argv = [sys.argv[0]]
import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "d2_dyn.py")).read().split("lux = [0.3")[0])
lux = [0.5, 1, 2, 5, 20]
print(" " * 46 + "".join(f"{l:>11g}k" for l in lux))
def row(label, **kw):
    print(f"{label:46s}" + "".join(f"{fmt(run(l, t_end=300, **kw)):>12s}" for l in lux)); sys.stdout.flush()
row("S6 C45 Q19 koff.45 (worst C, slow event)", C=45e-6, Qadv=19e-6)
row("S6 C45 Q19 koff.20", C=45e-6, Qadv=19e-6, k_off=0.20)
row("S6 C55 Q16.2 koff.20 leak0", C=55e-6, k_off=0.20, d2_leak=0)
row("S6 C55 Q16.2 koff.20 leak0 R2=3.3M", C=55e-6, k_off=0.20, d2_leak=0, R2=3.3e6)
row("S6 C45 Q19 koff.20 leak0 R2=3.3M", C=45e-6, Qadv=19e-6, k_off=0.20, d2_leak=0, R2=3.3e6)
row("S6 C55 1-channel Q6.2 koff.20 leak0", C=55e-6, Qadv=6.2e-6, k_off=0.20, d2_leak=0)
row("S6 C55 1-channel Q6.2 koff.45", C=55e-6, Qadv=6.2e-6)
row("S6 C55 +4dBm Q23.3 C45", C=45e-6, Qadv=23.3e-6)
