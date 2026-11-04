import sys, math, json; import os; HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from scenarios import SC, T
from teamtools import val
COLS='ABCDEFGHIJKLMNOPQ'
def xy(s):
    c=s[0]; r=int(s[1:])
    x={'@':-1,'R':17}.get(c, COLS.index(c) if c in COLS else None); return x, r
DIRS={0:(0,1),45:(1,1),90:(1,0),135:(1,-1),180:(0,-1),225:(-1,-1),270:(-1,0),315:(-1,1)}
def seg_cross(p,q,a,b):
    def o(p,q,r): return (q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0])
    d1,d2,d3,d4=o(a,b,p),o(a,b,q),o(p,q,a),o(p,q,b)
    return d1*d2<0 and d3*d4<0
def ray(start,ang):
    dx,dy=DIRS[ang]; return start,(start[0]+dx*30,start[1]+dy*30)
def point(frm,to):
    vx,vy=to[0]-frm[0],to[1]-frm[1]; a=math.degrees(math.atan2(vx,vy))%360
    return min(DIRS,key=lambda d: min(abs(d-a),360-abs(d-a)))
out={}; bad=0
for s in SC:
    errs=[]; occ={}
    O={k:xy(v) for k,v in s['O'].items()}
    for k,(x,r) in O.items():
        on = 0<=x<=16 and 1<=r<=14
        if k==s.get('inb'):
            if on: errs.append('inbounder on court')
            adj = (r==0 and 0<=x<=16) or (x in(-1,17) and 1<=r<=14)
            if not adj: errs.append('inbounder not beside an edge square')
        elif not on: errs.append(f'O{k} off board')
        occ.setdefault((x,r),[]).append(f'O{k}')
    ballp=O[s['ball']]; arrows={}
    for k,(sq,(mode,tgt)) in s['X'].items():
        p=xy(sq); occ.setdefault(p,[]).append(f'X{k}')
        if not (0<=p[0]<=16 and 1<=p[1]<=14): errs.append(f'X{k} off board')
        man=O[tgt]
        if mode in('man','ball'): a=point(p,man)
        elif mode=='help': a=point(p,ballp)
        else:
            (ax,ay),(bx,by)=ballp,man
            online = abs((bx-ax)*(p[1]-ay)-(by-ay)*(p[0]-ax))<1e-9 and min(ax,bx)<=p[0]<=max(ax,bx) and min(ay,by)<=p[1]<=max(ay,by)
            opts=list(DIRS) if online else [d for d in DIRS if seg_cross(*ray(p,d),ballp,man)]
            if not opts: errs.append(f'X{k} deny arrow cannot cross the lane'); a=point(p,man)
            else:
                want=point(p,man); a=min(opts,key=lambda d: min(abs(d-want),360-abs(d-want)))
        if mode=='ball' and max(abs(p[0]-man[0]),abs(p[1]-man[1]))!=1: errs.append(f'X{k} on the ball but not adjacent')
        arrows[k]=a
    for p,who in occ.items():
        if len(who)>1: errs.append('shared square '+'+'.join(who))
    offk=T[s['off']]
    open_ex=[k for k in offk if val(k,'shot_three')>=10 or val(k,'shot_layup')>=16]
    if not open_ex: errs.append('no player can make an open look Excellent')
    if s['kind']=='LATE CLOCK' and 'Three' in s['title'] and not any(val(k,'shot_three')>=10 for k in offk): errs.append('no 10+ three-point shooter')
    out[s['n']]=arrows
    print(f"{s['n']:2} {s['title']:24} {'OK' if not errs else 'FAIL: '+'; '.join(errs)}")
    bad+=bool(errs)
json.dump(out,open(os.path.join(HERE,'scenario_arrows.json'),'w'))
print('failures',bad)
