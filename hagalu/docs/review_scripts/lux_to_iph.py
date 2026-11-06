"""Daylight lux -> TEMD7000X01 photocurrent, from the ASTM G173 spectra (pvlib copy), a CIE V(lambda) fit and an
approximate Si PIN relative spectral response (Vishay Fig. 6 not machine-readable; two shapes bracket it)."""
import csv, sys, math
import numpy as np
rows = list(csv.reader(open(sys.argv[1])))[2:]
lam = np.array([float(r[0]) for r in rows]); glob = np.array([float(r[2]) for r in rows]); dirn = np.array([float(r[3]) for r in rows])
ext = np.array([float(r[1]) for r in rows])
def V(l):  # Wyman-Sloan-Shirley 2013 fit to CIE 1931 y-bar (= photopic V)
    def g(x, mu, s1, s2):
        s = np.where(x < mu, s1, s2); return np.exp(-0.5*((x-mu)/s)**2)
    return 0.821*g(l, 568.8, 46.9, 40.5) + 0.286*g(l, 530.9, 16.3, 31.1)
# Si PIN relative spectral sensitivity (A/W), normalised to 1 at the 900 nm peak
pts_typ = [(300,0),(350,0.05),(400,0.18),(450,0.32),(500,0.44),(550,0.54),(600,0.63),(650,0.71),(700,0.78),(750,0.85),
           (800,0.91),(850,0.96),(900,1.0),(950,0.93),(1000,0.68),(1050,0.33),(1100,0.10),(1120,0.05),(1150,0)]
def S_typ(l):
    x, y = zip(*pts_typ); return np.interp(l, x, y, left=0, right=0)
def S_ideal(l):  # constant QE 0.85 to 950 nm then falling (thin-ish Si), responsivity ~ lambda
    r = np.where(l <= 950, l/900, (950/900)*np.clip((1120-l)/170, 0, 1)); return np.where(l < 350, 0, r)
def integ(y): return np.trapezoid(y, lam)
IK = 3e-6  # A at 1 mW/cm2 (10 W/m2), 950 nm
def per_klx(E, S, name):
    lux = 683*integ(E*V(lam))
    W = integ(E); Wsi = integ(E*(lam < 1120))
    i = IK/(10*S(950.0)) * integ(E*S(lam))       # A for this spectrum
    return lux, W, i/(lux/1000)
def bb(T):
    h,c,k = 6.626e-34,2.998e8,1.381e-23; l = lam*1e-9
    return 1/(l**5*(np.exp(h*c/(l*k*T))-1))
def led(cct="4000K"):
    return 1.0*np.exp(-0.5*((lam-450)/10)**2) + 1.6*np.exp(-0.5*((lam-590)/55)**2)
spectra = [("AM1.5 global (sun + sky)", glob), ("AM1.5 direct beam", dirn), ("AM0 extraterrestrial", ext),
           ("blackbody 6500 K (overcast/shade proxy)", bb(6500)), ("blackbody 2850 K (incandescent/halogen)", bb(2850)),
           ("white LED ~4000 K (no IR)", led())]
for sname, S in (("typical PIN shape", S_typ), ("ideal-QE shape", S_ideal)):
    print(f"--- spectral response: {sname}; S(950)/S(900) = {S(950.0)/S(900.0):.2f}")
    for name, E in spectra:
        lux, W, ipk = per_klx(E, S, name)
        print(f"{name:42s} {lux/W:6.1f} lm/W(total)  -> {ipk*1e6:5.2f} uA per klx   ({W/lux*1e3:.2f} W/m2 per klx)")
