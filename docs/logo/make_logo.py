import math,sys
N=1080
def P(t): return math.sin(t)+2*math.sin(2*t), math.cos(t)-2*math.cos(2*t), -math.sin(3*t)
S=36; cx=128; cy=128+36*0.469
T=[2*math.pi*i/N for i in range(N+1)]
def xy(t):
    x,y,z=P(t); return cx+S*x, cy+S*y
A=(0xE3,0xA3,0x26); B=(0x27,0x33,0x78)
def col(t):
    f=(1-math.cos(t))/2
    return '#%02x%02x%02x'%tuple(round(A[k]+(B[k]-A[k])*f) for k in range(3))
# find crossings
cr=[]
for i in range(N):
    for j in range(i+N//12,N):
        if (N-j+i)<N//12: continue
        (x1,y1),(x2,y2)=xy(T[i]),xy(T[j])
        if (x1-x2)**2+(y1-y2)**2<0.6:
            ti,tj=T[i],T[j]
            over = ti if P(ti)[2]>P(tj)[2] else tj
            if all(abs(over-c)>0.2 for c in cr): cr.append(over)
print(len(cr),file=sys.stderr)
bg='#FBF5E9'; W=17; H=31
o=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">',
   f'<title>gantu-tag</title><rect width="256" height="256" rx="56" fill="{bg}"/>','<g fill="none" stroke-linecap="round" stroke-linejoin="round">']
step=3
for i in range(0,N,step):
    a=xy(T[i]); b=xy(T[min(i+step,N)])
    o.append(f'<line x1="{a[0]:.2f}" y1="{a[1]:.2f}" x2="{b[0]:.2f}" y2="{b[1]:.2f}" stroke="{col(T[i])}" stroke-width="{W}"/>')
for c in cr:
    pts=[xy(c+d*0.01) for d in range(-30,31)]
    d='M'+' L'.join(f'{x:.2f},{y:.2f}' for x,y in pts)
    o.append(f'<path d="{d}" stroke="{bg}" stroke-width="{H}" stroke-linecap="butt"/>')
    # redraw over strand in short colored pieces (no halo) so gradient continues
    for k in range(-33,33,3):
        a=xy(c+k*0.01); b=xy(c+(k+3)*0.01)
        o.append(f'<line x1="{a[0]:.2f}" y1="{a[1]:.2f}" x2="{b[0]:.2f}" y2="{b[1]:.2f}" stroke="{col(c+k*0.01)}" stroke-width="{W}"/>')
o.append('</g></svg>')
open('logo.svg','w').write('\n'.join(o))
