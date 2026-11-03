import sys, statistics as st, itertools; import os; HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from data import CARDS, OFF, DEF, parse
names=OFF+DEF; ix={n:i for i,n in enumerate(names)}
C={k:dict(n=n,role=role,tier=tier,qs=qs,v=[v for v,_ in parse(o)+parse(d)]) for k,n,role,tier,tag,qs,o,d in CARDS}
def val(k,n): return C[k]['v'][ix[n]]
med={n:st.median(val(k,n) for k in C) for n in names}
zones=[[('shot_layup','con_layup'),('shot_dunk','con_dunk'),('shot_post','con_post')],[('shot_floater','con_floater')],[('shot_mid','con_mid')],[('shot_long','con_long')],[('shot_three','con_three')]]
pts=lambda z: 3 if z[0][0]=='shot_three' else 2
def jobs(k):
    return dict(creator=val(k,'dribble')>=17 or val(k,'pass')>=17, shooter=val(k,'shot_three')>=10,
                anchor=val(k,'con_layup')>=10 or val(k,'con_dunk')>=11, stopper=val(k,'agility')>=8)
def team_stats(ks):
    off=st.mean(max(max(pts(z)*(val(k,s)-med[d]) for s,d in z) for k in ks) for z in zones)
    dfn=st.mean(st.mean(max(pts(z)*(med[s]-val(k,d)) for s,d in z) for k in ks) for z in zones)
    J=[jobs(k) for k in ks]
    cover=dict(creator=sum(j['creator'] for j in J)>=1, shooters=sum(j['shooter'] for j in J)>=2,
               anchor=sum(j['anchor'] for j in J)>=1, stopper=sum(j['stopper'] for j in J)>=1)
    return off, dfn, off-dfn, cover
