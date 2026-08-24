"""ITF-Knotenzeiten mit Knotendisziplin in BEIDEN Richtungen und Ankunfts-/Abfahrtsfenster."""
import numpy as np, math
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import lil_matrix
RES=0.07
def solve(rows, anchor=None, off_lo=2, off_hi=5, time_limit=900, mip_gap=1e-4):
    """rows: (a,b,T_base,_,w,fs,fi,fc). T_base = reine Fahrzeit Knoten->Knoten (ohne Halt)."""
    nodes=sorted({r[0] for r in rows}|{r[1] for r in rows}); IX={n:i for i,n in enumerate(nodes)}
    n=len(nodes); m=len(rows)
    T=[r[2] for r in rows]; W=[r[4] for r in rows]; L=[RES*t+2 for t in T]
    # Variablen
    PHI=0; A1=n; D1=2*n; A2=3*n; D2=4*n
    K1=5*n; K2=5*n+m; P1=5*n+2*m; P2=5*n+3*m; U1=5*n+4*m; U2=5*n+5*m
    N=5*n+6*m
    A=lil_matrix((4*m,N)); lb=np.zeros(4*m); ub=np.zeros(4*m)
    for e,(a,b,t,_p,w,*rest) in enumerate(rows):
        i,j=IX[a],IX[b]
        # Richtung 1: (phi_j - a1_j) - (phi_i + d1_i) + 30k1 - p1 = T
        A[e,PHI+j]=1; A[e,A1+j]=-1; A[e,PHI+i]=-1; A[e,D1+i]=-1; A[e,K1+e]=30; A[e,P1+e]=-1
        lb[e]=ub[e]=T[e]
        # Richtung 2
        A[m+e,PHI+i]=1; A[m+e,A2+i]=-1; A[m+e,PHI+j]=-1; A[m+e,D2+j]=-1; A[m+e,K2+e]=30; A[m+e,P2+e]=-1
        lb[m+e]=ub[m+e]=T[e]
        A[2*m+e,U1+e]=1; A[2*m+e,P1+e]=-1; lb[2*m+e]=-L[e]; ub[2*m+e]=np.inf
        A[3*m+e,U2+e]=1; A[3*m+e,P2+e]=-1; lb[3*m+e]=-L[e]; ub[3*m+e]=np.inf
    c=np.zeros(N)
    for e in range(m):
        c[P1+e]=0.15*W[e]; c[P2+e]=0.15*W[e]; c[U1+e]=2.0*W[e]; c[U2+e]=2.0*W[e]
    vlb=np.zeros(N); vub=np.zeros(N); integ=np.zeros(N)
    for i in range(n):
        vub[PHI+i]=29; integ[PHI+i]=1
        for off in (A1,D1,A2,D2):
            vlb[off+i]=off_lo; vub[off+i]=off_hi; integ[off+i]=1
    for e in range(m):
        span=math.ceil((T[e]+90)/30)+2
        for K in (K1,K2): vlb[K+e]=-span; vub[K+e]=span; integ[K+e]=1
        vub[P1+e]=29; vub[P2+e]=29; vub[U1+e]=np.inf; vub[U2+e]=np.inf
    if anchor and anchor in IX: vlb[PHI+IX[anchor]]=vub[PHI+IX[anchor]]=0
    r=milp(c=c,constraints=LinearConstraint(A.tocsr(),lb,ub),bounds=Bounds(vlb,vub),
           integrality=integ,options={'time_limit':time_limit,'mip_rel_gap':mip_gap,'presolve':True})
    if r.x is None: return None
    x=r.x
    phi={nodes[i]:int(round(x[PHI+i]))%30 for i in range(n)}
    off={nodes[i]:{'a1':int(round(x[A1+i])),'d1':int(round(x[D1+i])),
                   'a2':int(round(x[A2+i])),'d2':int(round(x[D2+i]))} for i in range(n)}
    out=[]; ws=0.;wr=0.;band=0.
    for e,(a,b,t,_p,w,fs,fi,fc) in enumerate(rows):
        p1=int(round(x[P1+e])); p2=int(round(x[P2+e]))
        r1=t+p1; r2=t+p2
        ws+=2*w; wr+=w*(p1/t*100 + p2/t*100); band+= (w if p1/t<=RES else 0)+(w if p2/t<=RES else 0)
        out.append((a,b,t,r1,r2,p1,p2,round(p1/t*100,1),round(p2/t*100,1),w,fs,fi,fc))
    return {'kosten':round(r.fun,1),'status':r.status,'optimal':r.status==0,'phi':phi,'offsets':off,
            'kanten':out,'reserve_pct':round(wr/ws,2),'sollband_pct':round(100*band/ws,1),
            'gewicht':round(ws/2,1),'kosten_je_gewicht':round(r.fun/(ws/2),3)}
