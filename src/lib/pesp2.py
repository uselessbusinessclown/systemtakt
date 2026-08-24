"""PESP mit korrekt bestrafter Beschleunigung: d = dp - dm, Kosten 0.15*dp + 2*u + ACC*dm."""
import numpy as np, math
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import lil_matrix
DW, RES = 6, 0.07
def solve(rows, anchor=None, max_acc=0, acc_cost=4.0, time_limit=900, mip_gap=1e-4):
    nodes=sorted({r[0] for r in rows}|{r[1] for r in rows}); IX={n:i for i,n in enumerate(nodes)}
    n=len(nodes); m=len(rows)
    T0=[r[2]+DW for r in rows]; W=[r[4] for r in rows]; L=[RES*t+2 for t in T0]
    P,K,DP,DM,U = 0, n, n+m, n+2*m, n+3*m
    N=n+4*m
    A=lil_matrix((2*m,N)); lb=np.zeros(2*m); ub=np.zeros(2*m)
    for e in range(m):
        a,b=rows[e][0],rows[e][1]; i,j=IX[a],IX[b]
        A[e,P+j]=1; A[e,P+i]=-1; A[e,K+e]=30; A[e,DP+e]=-1; A[e,DM+e]=1
        lb[e]=ub[e]=T0[e]
        A[m+e,U+e]=1; A[m+e,DP+e]=-1
        lb[m+e]=-L[e]; ub[m+e]=np.inf
    c=np.zeros(N)
    for e in range(m):
        c[DP+e]=0.15*W[e]; c[U+e]=2.0*W[e]; c[DM+e]=acc_cost*W[e]
    vlb=np.zeros(N); vub=np.zeros(N); integ=np.zeros(N)
    for i in range(n): vub[P+i]=29; integ[P+i]=1
    for e in range(m):
        span=math.ceil((T0[e]+60)/30)+2
        vlb[K+e]=-span; vub[K+e]=span; integ[K+e]=1
        vub[DP+e]=29; vub[DM+e]=max_acc; vub[U+e]=np.inf
    if anchor and anchor in IX: vlb[P+IX[anchor]]=vub[P+IX[anchor]]=0
    r=milp(c=c,constraints=LinearConstraint(A.tocsr(),lb,ub),bounds=Bounds(vlb,vub),
           integrality=integ,options={'time_limit':time_limit,'mip_rel_gap':mip_gap,'presolve':True})
    if r.x is None: return None
    x=r.x; phi={nodes[i]:int(round(x[P+i]))%30 for i in range(n)}
    out=[]; band=0.;ws=0.;wr=0.;acc=0;mx=0
    for e in range(m):
        a,b,t,p15,w = rows[e][0],rows[e][1],rows[e][2],rows[e][3],rows[e][4]
        d=int(round(x[DP+e]-x[DM+e])); ts=T0[e]+d-DW; rr=(ts-t)/t*100 if t else 0
        ws+=w; wr+=w*max(rr,0); mx=max(mx,d)
        if d<0: acc+=1
        if 0<=rr<=7: band+=w
        out.append((a,b,t,p15,ts,d,round(rr,1),w)+tuple(rows[e][5:]))
    return {'kosten':round(r.fun,1),'status':r.status,'phi':phi,'kanten':out,'beschl':acc,
            'sollband_pct':round(100*band/ws,1),'reserve_pct':round(wr/ws,2),'gewicht':round(ws,1),
            'max_zuschlag':mx,'kosten_je_gewicht':round(r.fun/ws,3),'optimal':r.status==0}
