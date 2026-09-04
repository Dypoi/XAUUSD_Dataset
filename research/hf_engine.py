"""Engine multi-posisi paralel + time stop -> memungkinkan frekuensi tinggi."""
import pandas as pd, numpy as np
from numba import njit

@njit
def sim_par(sig,ob,oa,hb,lb,ha,la,dayid,sl_usd,rr,risk_usd,eq0,
            max_conc,max_day,timestop,slip,dl,dp):
    n=len(sig)
    # slot posisi
    a_open=np.zeros(max_conc,np.int64); a_side=np.zeros(max_conc,np.int64)
    a_ep=np.zeros(max_conc); a_sl=np.zeros(max_conc); a_t1=np.zeros(max_conc)
    a_t2=np.zeros(max_conc); a_lot=np.zeros(max_conc); a_rem=np.zeros(max_conc)
    a_h1=np.zeros(max_conc,np.int64); a_bar=np.zeros(max_conc,np.int64)
    a_acc=np.zeros(max_conc)   # akumulasi PnL USD termasuk partial
    et=np.empty(n*2,np.int64); xt=np.empty(n*2,np.int64); pnl=np.empty(n*2)
    sd=np.empty(n*2,np.int64); eqa=np.empty(n*2)
    N=0; eq=eq0; cur_day=-1; ntoday=0; pnl_today=0.0
    for i in range(n):
        if dayid[i]!=cur_day:
            cur_day=dayid[i]; ntoday=0; pnl_today=0.0
        # --- kelola posisi terbuka ---
        for s_ in range(max_conc):
            if a_open[s_]==0: continue
            side=a_side[s_]; closed=0; got=0.0
            if side>0:
                if lb[i]<=a_sl[s_]:
                    got=a_rem[s_]*((a_sl[s_]-slip)-a_ep[s_]); closed=1
                else:
                    if a_h1[s_]==0 and hb[i]>=a_t1[s_]:
                        got+=0.5*(a_t1[s_]-a_ep[s_]); a_rem[s_]=0.5; a_h1[s_]=1
                        a_sl[s_]=a_ep[s_]+(oa[i]-ob[i])
                    if a_h1[s_]==1 and hb[i]>=a_t2[s_]:
                        got+=a_rem[s_]*(a_t2[s_]-a_ep[s_]); closed=1
            else:
                if ha[i]>=a_sl[s_]:
                    got=a_rem[s_]*(a_ep[s_]-(a_sl[s_]+slip)); closed=1
                else:
                    if a_h1[s_]==0 and la[i]<=a_t1[s_]:
                        got+=0.5*(a_ep[s_]-a_t1[s_]); a_rem[s_]=0.5; a_h1[s_]=1
                        a_sl[s_]=a_ep[s_]-(oa[i]-ob[i])
                    if a_h1[s_]==1 and la[i]<=a_t2[s_]:
                        got+=a_rem[s_]*(a_ep[s_]-a_t2[s_]); closed=1
            a_bar[s_]+=1
            if closed==0 and a_bar[s_]>=timestop:
                mp=(hb[i]+lb[i])/2 if side>0 else (ha[i]+la[i])/2
                got+=a_rem[s_]*((mp-a_ep[s_]) if side>0 else (a_ep[s_]-mp)); closed=1
            if got!=0.0 or closed==1:
                usd=got*a_lot[s_]*100.0
                eq+=usd; pnl_today+=usd
                a_acc[s_]+=usd
                if closed==1:
                    et[N]=a_open[s_]; xt[N]=i; pnl[N]=a_acc[s_]; sd[N]=side; eqa[N]=eq; N+=1
                    a_open[s_]=0; a_acc[s_]=0.0
        # --- entry baru ---
        if sig[i]!=0 and i<n-1 and eq>0:
            if ntoday<max_day and pnl_today>-dl and pnl_today<dp:
                slot=-1
                for s_ in range(max_conc):
                    if a_open[s_]==0: slot=s_; break
                if slot>=0:
                    j=i+1; spread=oa[j]-ob[j]
                    sl_eff=sl_usd+spread+slip
                    lot=risk_usd/(sl_eff*100.0)
                    if lot<0.01: lot=0.01
                    if lot>50.0: lot=50.0
                    side=sig[i]
                    if side>0:
                        ep=oa[j]+slip; a_sl[slot]=ep-sl_usd; a_t1[slot]=ep+sl_usd; a_t2[slot]=ep+rr*sl_usd
                    else:
                        ep=ob[j]-slip; a_sl[slot]=ep+sl_usd; a_t1[slot]=ep-sl_usd; a_t2[slot]=ep-rr*sl_usd
                    a_open[slot]=j; a_side[slot]=side; a_ep[slot]=ep; a_lot[slot]=lot
                    a_rem[slot]=1.0; a_h1[slot]=0; a_bar[slot]=0; a_acc[slot]=0.0
                    ntoday+=1
    return et[:N],xt[:N],pnl[:N],sd[:N],eqa[:N]
