import sys,math; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from sexp import parse
F=sys.argv[1] if len(sys.argv)>1 else '/home/alex/prjs/ames/switch/pocketbeagle2_ethernet_cap/io.kicad_sch'
S=parse(open(F).read())
def kids(x,k): return [y for y in x if isinstance(y,list) and y and y[0]==k]
def fnd(x,k):
    out=[]
    if isinstance(x,list):
        if x and x[0]==k: out.append(x)
        for y in x: out+=fnd(y,k)
    return out
R=lambda v: round(v,2)
libs={l[1].strip('"'):l for l in kids(kids(S,'lib_symbols')[0],'symbol')}
syms=kids(S,'symbol')
def ref(s): return [p[2].strip('"') for p in kids(s,'property') if p[1]=='"Reference"'][0]
def uuid(x): u=kids(x,'uuid'); return u[0][1].strip('"') if u else None
def pinpos(s,num):
    lib=libs[kids(s,'lib_id')[0][1].strip('"')]
    at=kids(s,'at')[0]; X,Y,Rr=float(at[1]),float(at[2]),float(at[3]) if len(at)>3 else 0
    mir=kids(s,'mirror')
    for p in fnd(lib,'pin'):
        n=kids(p,'number')
        if n and n[0][1].strip('"')==num:
            a=kids(p,'at')[0]; px,py=float(a[1]),-float(a[2])
            if mir and mir[0][1]=='x': py=-py
            if mir and mir[0][1]=='y': px=-px
            t=math.radians(Rr); rx=px*math.cos(t)+py*math.sin(t); ry=-px*math.sin(t)+py*math.cos(t)
            return (R(X+rx),R(Y+ry))
symd={ref(s):s for s in syms}
wires=[(uuid(w),[(R(float(p[1])),R(float(p[2]))) for p in fnd(w,'xy')]) for w in kids(S,'wire')]
juncs=[(uuid(j),(R(float(kids(j,'at')[0][1])),R(float(kids(j,'at')[0][2])))) for j in kids(S,'junction')]
labels=[(l[0],l[1].strip('"'),(R(float(kids(l,'at')[0][1])),R(float(kids(l,'at')[0][2]))),uuid(l)) for l in S if isinstance(l,list) and l and l[0] in('label','global_label','hierarchical_label')]
pwr=[(ref(s),kids(s,'lib_id')[0][1].strip('"'),(R(float(kids(s,'at')[0][1])),R(float(kids(s,'at')[0][2]))),uuid(s)) for s in syms if ref(s).startswith(('#PWR','#FLG'))]
allpins={}
for s in syms:
    r=ref(s)
    if r.startswith('#'): continue
    lib=libs[kids(s,'lib_id')[0][1].strip('"')]
    for p in fnd(lib,'pin'):
        n=kids(p,'number')
        if n: allpins[pinpos(s,n[0][1].strip('"'))]=(r,n[0][1].strip('"'))
def group(pt):
    """connected wire cluster from pt"""
    seen={pt}; fr=[pt]; ws=set()
    while fr:
        q=fr.pop()
        for u,w in wires:
            a,b=w
            on = q in (a,b) or (a[0]==b[0]==q[0] and min(a[1],b[1])<=q[1]<=max(a[1],b[1])) or (a[1]==b[1]==q[1] and min(a[0],b[0])<=q[0]<=max(a[0],b[0]))
            if on and u not in ws:
                ws.add(u)
                for e in (a,b):
                    if e not in seen: seen.add(e); fr.append(e)
        # junction/pins on wire bodies
    return seen,ws
