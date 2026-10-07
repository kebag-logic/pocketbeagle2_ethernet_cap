import sys,math; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from model import *
MIL=0.0254
MOD={'RD0':1808.5,'RD1':1520.17,'RD2':1511.44,'RD3':1459.68,'RX_CLK':2204.81,'RX_CTRL':1350.87,
     'TD0':1182.32,'TD1':1991.72,'TD2':785.48,'TD3':328.86,'TX_CLK':2442.23,'TX_CTRL':2925.95}
# (phy-side net, pb2-side net, series R)
LINES={'RD0':('RX_D0','/RGMII_RD0_PHY_to_CPU','R16'),'RD1':('RX_D1','/RGMII_RD1_PHY_to_CPU','R17'),
 'RD2':('RX_D2','/RGMII_RD2_PHY_to_CPU','R18'),'RD3':('RX_D3','/RGMII_RD3_PHY_to_CPU','R19'),
 'RX_CLK':('RX_CLK','/RGMII_RX_CLK_PHY_to_CPU','R15'),'RX_CTRL':('RX_CTRL','/RGMII_RX_CTRL_PHY_to_CPU','R12'),
 'TD0':('TX_D0','/RGMII_TD0_CPU_to_PHY','R8'),'TD1':('TX_D1','/RGMII_TD1_CPU_to_PHY','R9'),
 'TD2':('TX_D2','/RGMII_TD2_CPU_to_PHY','R10'),'TD3':('TX_D3','/RGMII_TD3_CPU_to_PHY','R11'),
 'TX_CLK':('GTX_CLK','/RGMII_TX_CLK_CPU_to_PHY','R14'),'TX_CTRL':('TX_EN_TX_CTRL','/RGMII_TX_CTRL_CPU_to_PHY','R13')}
def measure(tr,pads):
    out={}
    netsR={}
    for p in pads: netsR.setdefault(p.net,[]).append(p)
    for k,(phy,pb,r) in LINES.items():
        # phy-side net name contains phy token
        phynets=[n for n in {t['net'] for t in tr} if phy in n and 'U2' in n] or [p.net for p in pads if p.ref==r and p.net!=pb]
        L={}
        for n in set(phynets+[pb]):
            segs=[t for t in tr if t['kind']=='seg' and t['net']==n and t['layer'] in ('F.Cu','B.Cu')]
            vias=[t for t in tr if t['kind']=='via' and t['net']==n]
            L[n]=(sum(math.dist(*t['pts']) for t in segs),len(vias))
        out[k]=L
    return out
if __name__=='__main__':
    pads,fps,tr=load()
    res=measure(tr,pads)
    for k,L in res.items():
        tot=sum(v[0] for v in L.values()); nv=sum(v[1] for v in L.values())
        print(f"{k:8s} cape {tot:6.2f} mm vias {nv}  module {MOD[k]*MIL:6.2f} mm   nets {[(n[-22:],round(v[0],2)) for n,v in L.items()]}")
