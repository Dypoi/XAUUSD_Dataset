"""Event-driven M1 backtest engine for XAUUSD (bid/ask aware)."""
import numpy as np, pandas as pd
from numba import njit

@njit(cache=True)
def run(entry_idx, side, tp_dist, sl_dist, max_bars,
        hb, lb, cb, ha, la, ca, ob, oa, comm_usd, max_open, slip):
    n=len(entry_idx)
    e_t=np.empty(n,np.int64); x_t=np.empty(n,np.int64); keep=np.empty(n,np.int64)
    e_p=np.empty(n); x_p=np.empty(n); pnl=np.empty(n); reason=np.empty(n,np.int64)
    k=0; free_at=-1
    for i in range(n):
        s=entry_idx[i]
        if s+1>=len(cb): break
        if s<=free_at:   # position already open (single position mode)
            continue
        j=s+1
        if side[i]>0:
            ep=oa[j]+slip
            tp=ep+tp_dist[i]; sl=ep-sl_dist[i]
        else:
            ep=ob[j]-slip
            tp=ep-tp_dist[i]; sl=ep+sl_dist[i]
        xp=0.0; xt=-1; rs=0
        end=j+max_bars
        if end>=len(cb): end=len(cb)-1
        for t in range(j,end+1):
            if side[i]>0:
                # exit on bid
                if lb[t]<=sl:
                    xp=sl-slip; xt=t; rs=1
                    if hb[t]>=tp and ob[t]>=tp: # ambiguous: assume SL first (conservative)
                        pass
                    break
                if hb[t]>=tp:
                    xp=tp; xt=t; rs=2; break
            else:
                if ha[t]>=sl:
                    xp=sl+slip; xt=t; rs=1; break
                if la[t]<=tp:
                    xp=tp; xt=t; rs=2; break
        if xt<0:
            xt=end
            xp=(cb[xt]-slip) if side[i]>0 else (ca[xt]+slip)
            rs=3
        g=(xp-ep) if side[i]>0 else (ep-xp)
        keep[k]=i; e_t[k]=j; x_t[k]=xt; e_p[k]=ep; x_p[k]=xp; pnl[k]=g-comm_usd; reason[k]=rs
        k+=1; free_at=xt
    return keep[:k],e_t[:k],x_t[:k],e_p[:k],x_p[:k],pnl[:k],reason[:k]
