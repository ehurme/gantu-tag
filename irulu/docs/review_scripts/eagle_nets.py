import sys, xml.etree.ElementTree as ET
t = ET.parse(sys.argv[1]); r = t.getroot()
parts = {}
for p in r.iter('part'):
    parts[p.get('name')] = (p.get('deviceset'), p.get('device'), p.get('value'))
nets = {}
for n in r.iter('net'):
    name = n.get('name')
    for pr in n.iter('pinref'):
        nets.setdefault(name, set()).add((pr.get('part'), pr.get('pin')))
for name in sorted(nets):
    members = sorted(nets[name])
    if any(m[0].startswith('U') or m[0].startswith('Y') or m[0].startswith('C') or m[0].startswith('R') or m[0].startswith('J') or m[0].startswith('E') for m in members):
        print(name, ':', ', '.join(f"{a}.{b}" for a,b in members))
print()
for k,v in sorted(parts.items()):
    if v[0] and not v[0].startswith(('FRAME','LOGO','FIDUCIAL','STAND','OSHW','SFE_LOGO','REVISION','WEB')):
        print(k, v)
