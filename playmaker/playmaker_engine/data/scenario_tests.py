import sys, json; import os; HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from scenarios import SC, T
from teamtools import val, C
Z=json.load(open(os.path.join(HERE,'court_zones.json')))
COLS='ABCDEFGHIJKLMNOPQ'
def xy(s): c=s[0]; return ({'@':-1,'R':17}.get(c, COLS.index(c) if c in COLS else 0), int(s[1:]))
def name(p): return f'{COLS[p[0]]}{p[1]}'
def on(p): return 0<=p[0]<=16 and 1<=p[1]<=14
SHOTS={'K':[('shot_layup','con_layup'),('shot_dunk','con_dunk'),('shot_post','con_post')],'M':[('shot_mid','con_mid'),('shot_floater','con_floater')],
       'L':[('shot_long','con_long')],'3':[('shot_three','con_three')]}
D8=[(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]
def reach(p,qs,occ,locked=False):
    """squares reachable with one movement action: Move, Quick Step or Sprint (paths must be clear)."""
    out={p}
    def line(d,n):
        q=p; res=[]
        for _ in range(n):
            q=(q[0]+d[0],q[1]+d[1])
            if not on(q) or q in occ: break
            res.append(q)
        return res
    for d in D8:
        diag=d[0]!=0 and d[1]!=0
        out|=set(line(d,qs))                                   # Quick Step
        if not locked:
            out|=set(line(d,(2 if diag else 3)))               # Move straight
            out|=set(line(d,(2 if diag else 3)+qs))            # Sprint
    if not locked:                                             # Move 1 straight + 1 diagonal
        for a in D8[:4]:
            m=(p[0]+a[0],p[1]+a[1])
            if on(m) and m not in occ:
                for b in D8[4:]:
                    q=(m[0]+b[0],m[1]+b[1])
                    if on(q) and q not in occ: out.add(q)
    return out
RIM=(8,2)
def dist(p): return max(abs(p[0]-RIM[0]),abs(p[1]-RIM[1]))
def adj(a,b): return max(abs(a[0]-b[0]),abs(a[1]-b[1]))==1
def best_shot(s, shooter_key, sp, X, occ_x, three_only=False):
    z=Z.get(name(sp),'.')
    if z=='.' or (three_only and z!='3'): return -99,None
    pts=3 if z=='3' else 2; best=(-99,None)
    for sk,ck in SHOTS[z]:
        r=val(shooter_key,sk)
        # defence reaction: one defender may make one movement; then the best adjacent contest
        def contest(dk,dp): return val(dk,ck)-(3 if dist(dp)>dist(sp) else 0)
        base=[contest(dk,dp) for dk,dp in X if adj(dp,sp)]
        cmax=max(base+[0])
        for dk,dp in X:
            occ=(occ_x-{dp})|{sp}
            for q in reach(dp,C[dk]['qs'],occ):
                if adj(q,sp): cmax=max(cmax,contest(dk,q))
        v=pts*(r-cmax)
        if v>best[0]: best=(v,f'{sk[5:]} {r}-{cmax}')
    return best
res={}
for s in SC:
    off=T[s['off']]; dfn=T[s['dfn']]
    O={k:xy(v) for k,v in s['O'].items()}; X=[(dfn[k-1],xy(sq)) for k,(sq,_) in s['X'].items()]
    occ_all={p for p in O.values()}|{p for _,p in X}; occ_x={p for _,p in X}
    three_only='Need a Three' in s['title']
    # Test B: first-turn gift
    if s.get('inb') or 'Hold for One' in s['title']:
        gift='n/a (rule: no first-turn shot)'; gv=None
    else:
        bk=s['ball']; sk=off[bk-1]; sp=O[bk]
        gv=-99; how=''
        for q in reach(sp,C[sk]['qs'],occ_all-{sp},locked=s.get('locked')==bk):
            v,h=best_shot(s,sk,q,X,occ_x,three_only)
            if v>gv: gv,how=v,f'O{bk} to {name(q)}: {h}'
        gift=f'best {gv} ({how})'
    # Test A (optimistic): best open-look ceiling for any offence player against current defence after one reaction
    top=-99; tw=''
    for k,p in O.items():
        if not on(p): continue
        sk=off[k-1]
        for q in reach(p,C[sk]['qs'],occ_all-{p}):
            v,h=best_shot(s,sk,q,X,occ_x,three_only)
            if v>top: top,tw=v,f'O{k} to {name(q)}: {h}'
    ok_b = gv is None or gv<30
    print(f"{s['n']:2} {s['title']:24} first-turn {'PASS' if ok_b else 'GIFT'}: {gift}\n   reachable ceiling {top} ({tw})")
