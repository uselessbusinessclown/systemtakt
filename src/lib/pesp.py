"""Exakte Lösung des Taktknoten-Problems als gemischt-ganzzahliges Programm (HiGHS)."""
import numpy as np, math
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import lil_matrix
DW, RES = 6, 0.07
def solve_exact(rows, anchor=None, max_acc=0, prio=None, prio_factor=1.0,
                time_limit=600, mip_gap=1e-4, fixed=None):
    """rows: (a,b,t_min,t_p15,w,fs,fi,fc).  max_acc: erlaubte Verkürzung in min (0 = neubaufrei)."""
    nodes=sorted({r[0] for r in rows}|{r[1] for r in rows}); IX={n:i for i,n in enumerate(nodes)}
    n=len(nodes); m=len(rows)
    T0=[r[2]+DW for r in rows]
    W=[(r[4]*prio_factor if (prio and (r[0]==prio or r[1]==prio)) else r[4]) for r in rows]
    L=[RES*t+2 for t in T0]
    # Variablen: phi(n) | k(m) | d(m) | u(m)
    P,K,Dv,U = 0, n, n+m, n+2*m
    N = n+3*m
    A=lil_matrix((2*m, N)); lb=np.zeros(2*m); ub=np.zeros(2*m)
    for e,(a,b,t,p15,w,fs,fi,fc) in enumerate(rows):
        i,j=IX[a],IX[b]
        A[e,P+j]=1; A[e,P+i]=-1; A[e,K+e]=30; A[e,Dv+e]=-1
        lb[e]=ub[e]=T0[e]                       # phi_j - phi_i + 30k - d = T0
        A[m+e,U+e]=1; A[m+e,Dv+e]=-1
        lb[m+e]=-L[e]; ub[m+e]=np.inf           # u >= d - L
    c=np.zeros(N)
    for e in range(m):
        c[Dv+e]=0.15*W[e]; c[U+e]=2.0*W[e]
    vlb=np.zeros(N); vub=np.zeros(N); integ=np.zeros(N)
    for i in range(n): vlb[P+i]=0; vub[P+i]=29; integ[P+i]=1
    for e in range(m):
        span=math.ceil((T0[e]+60)/30)+2
        vlb[K+e]=-span; vub[K+e]=span; integ[K+e]=1
        vlb[Dv+e]=-max_acc; vub[Dv+e]=29
        vlb[U+e]=0; vub[U+e]=np.inf
    if anchor and anchor in IX: vlb[P+IX[anchor]]=vub[P+IX[anchor]]=0
    for k,v in (fixed or {}).items():
        if k in IX: vlb[P+IX[k]]=vub[P+IX[k]]=v
    res=milp(c=c, constraints=LinearConstraint(A.tocsr(), lb, ub),
             bounds=Bounds(vlb,vub), integrality=integ,
             options={'time_limit':time_limit,'mip_rel_gap':mip_gap,'presolve':True,'disp':False})
    if res.x is None: return None
    x=res.x; phi={nodes[i]:int(round(x[P+i]))%30 for i in range(n)}
    out=[]; band=0.0; wsum=0.0; wres=0.0; acc=0; maxpad=0
    for e,(a,b,t,p15,w,fs,fi,fc) in enumerate(rows):
        d=int(round(x[Dv+e])); ts=T0[e]+d-DW; r=(ts-t)/t*100 if t else 0
        wsum+=w; wres+=w*max(r,0); maxpad=max(maxpad,d)
        if d<0: acc+=1
        if 0<=r<=7: band+=w
        out.append((a,b,t,p15,ts,d,round(r,1),w,fs,fi,fc))
    return {'kosten':round(res.fun,1),'status':res.status,'message':res.message,
            'gap_geschlossen':res.status==0,'phi':phi,'kanten':out,'beschl':acc,
            'sollband_pct':round(100*band/wsum,1),'reserve_pct':round(wres/wsum,2),
            'gewicht':round(wsum,1),'max_zuschlag':maxpad,'kosten_je_gewicht':round(res.fun/wsum,3)}
