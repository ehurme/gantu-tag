import numpy as np
# Murata GRM21BR60J107ME15 SPICE model (0 V DC, 25 C, small signal)
def Zpar(*zs):
    return 1/sum(1/z for z in zs)
def Z(f):
    w = 2*np.pi*f; j=1j
    C=lambda c: 1/(j*w*c); L=lambda l: j*w*l
    z = Zpar(C(7.31e-05), 5.00e+05)
    z += L(1.95e-10)
    z += 1.33e-03
    z += Zpar(C(4.16e-03), 8.33e-01)
    z += Zpar(C(5.06e-03), 6.43e-02)
    z += Zpar(C(4.91e-03), 1.09e-02)
    z += Zpar(C(8.50e-03), 5.04e-04)
    z += Zpar(L(1.53e-11), 6.08e-02)
    z += Zpar(L(2.67e-11), 2.12e-02)
    z += Zpar(L(7.82e-11), 1.23e-02)
    z += Zpar(L(4.17e-10), 6.65e-03)
    z += Zpar(C(1.73e-04), L(1.28e-10), 1.08e-03)
    z += Zpar(C(1.53e-04), L(8.20e-11), 8.47e-04)
    z += Zpar(C(3.16e-11), L(4.12e-11), 2.24e+00)
    return z
for f in (100,120,1e3,1e4,1e5,1e6):
    z=Z(f); c=-1/(2*np.pi*f*z.imag)
    print(f"{f:>8g} Hz  Ceff={c*1e6:6.1f} uF  ESR={z.real*1e3:7.2f} mohm |Z|={abs(z):.4f}")
