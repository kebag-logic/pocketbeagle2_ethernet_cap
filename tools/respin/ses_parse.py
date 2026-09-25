import re,sys
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from sexp import parse
def load(path):
    t=parse(open(path).read())
    def fnd(x,k):
        out=[]
        if isinstance(x,list):
            if x and x[0]==k: out.append(x)
            for y in x: out+=fnd(y,k)
        return out
    res=fnd(t,'resolution')[0]; scale=float(res[2])
    nets={}
    for n in fnd(fnd(t,'network_out')[0],'net'):
        name=n[1].strip('"'); items=[]
        for w in [x for x in n if isinstance(x,list) and x[0]=='wire']:
            p=w[1]; lay=p[1]; wd=float(p[2])/scale
            v=list(map(float,[a for a in p[3:] if not isinstance(a,list)]))
            items.append(('seg',lay,wd,[(v[i]/scale,-v[i+1]/scale) for i in range(0,len(v),2)]))
        for v in [x for x in n if isinstance(x,list) and x[0]=='via']:
            items.append(('via',float(v[2])/scale,-float(v[3])/scale))
        nets[name]=items
    return nets
