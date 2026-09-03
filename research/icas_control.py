import pandas as pd, numpy as np, importlib.util, sys
spec=importlib.util.spec_from_file_location("ir","icas_replicate.py")
# jalankan ulang pembentukan data tanpa print
import numpy as np, pandas as pd
from numba import njit
d=pd.read_parquet('m1.parquet').set_index('timestamp').sort_index()
m5=pd.DataFrame({
 'o':((d.open_bid+d.open_ask)/2).resample('5min').first(),
 'h':((d.high_bid+d.high_ask)/2).resample('5min').max(),
 'l':((d.low_bid+d.low_ask)/2).resample('5min').min(),
 'c':((d.close_bid+d.close_ask)/2).resample('5min').last(),
 'ob':d.open_bid.resample('5min').first(),'oa':d.open_ask.resample('5min').first(),
 'hb':d.high_bid.resample('5min').max(),'la':d.low_ask.resample('5min').min(),
 'lb':d.low_bid.resample('5min').min(),'ha':d.high_ask.resample('5min').max(),
}).dropna()
day=m5.index.normalize(); hh=m5.index.hour
asia=(hh<7); lon=(hh>=7)&(hh<12)
ah=m5.h.where(asia).groupby(day).cummax().ffill(); al=m5.l.where(asia).groupby(day).cummin().ffill()
lh=m5.h.where(lon).groupby(day).cummax().ffill(); ll=m5.l.where(lon).groupby(day).cummin().ffill()
BSL=pd.concat([ah,lh],axis=1).max(axis=1); SSL=pd.concat([al,ll],axis=1).min(axis=1)
# ---- versi BOCOR (replika bug F-18): agregat SEHARIAN ditempel ke semua bar
ahL=m5.h.where(asia).groupby(day).transform('max'); alL=m5.l.where(asia).groupby(day).transform('min')
lhL=m5.h.where(lon).groupby(day).transform('max'); llL=m5.l.where(lon).groupby(day).transform('min')
BSL_L=pd.concat([ahL,lhL],axis=1).max(axis=1).groupby(day).ffill().bfill()
SSL_L=pd.concat([alL,llL],axis=1).min(axis=1).groupby(day).ffill().bfill()
sw_h=m5.h.shift(2).rolling(5).max(); sw_l=m5.l.shift(2).rolling(5).min()
bfvg=m5.l>(m5.h.shift(2)+0.30); sfvg=m5.h<(m5.l.shift(2)-0.30)
def mk(BS,SS):
    b=((m5.l.shift(1)<=SS)|(m5.l.shift(2)<=SS))&(m5.c>m5.o)&((m5.c>sw_h)|bfvg)
    s=((m5.h.shift(1)>=BS)|(m5.h.shift(2)>=BS))&(m5.c<m5.o)&((m5.c<sw_l)|sfvg)
    return np.where(b.fillna(False),1,np.where(s.fillna(False),-1,0)).astype(np.int64)
@njit(cache=True)
def sim(sig,ob,oa,hb,lb,ha,la,sl_d,tp1,tp2,tp3,slip):
    n=len(sig);N=0
    et=np.empty(n,np.int64);xt=np.empty(n,np.int64);pnl=np.empty(n);sd=np.empty(n,np.int64)
    i=0
    while i<n-1:
        s=sig[i]
        if s==0: i+=1; continue
        j=i+1
        if j>=n: break
        if s>0: ep=oa[j]+slip; SL=ep-sl_d;T1=ep+tp1;T2=ep+tp2;T3=ep+tp3
        else:   ep=ob[j]-slip; SL=ep+sl_d;T1=ep-tp1;T2=ep-tp2;T3=ep-tp3
        rem=1.0;acc=0.0;k=j;done=-1;h1=False;h2=False;h3=False
        while k<n and k<j+2000:
            if s>0:
                if lb[k]<=SL: acc+=rem*((SL-slip)-ep); done=k; break
                if not h1 and hb[k]>=T1: acc+=0.30*(T1-ep);rem-=0.30;h1=True
                if not h2 and hb[k]>=T2: acc+=0.25*(T2-ep);rem-=0.25;h2=True
                if not h3 and hb[k]>=T3: acc+=0.25*(T3-ep);rem-=0.25;h3=True;SL=T1
            else:
                if ha[k]>=SL: acc+=rem*(ep-(SL+slip)); done=k; break
                if not h1 and la[k]<=T1: acc+=0.30*(ep-T1);rem-=0.30;h1=True
                if not h2 and la[k]<=T2: acc+=0.25*(ep-T2);rem-=0.25;h2=True
                if not h3 and la[k]<=T3: acc+=0.25*(ep-T3);rem-=0.25;h3=True;SL=T1
            if rem<=0.001: done=k; break
            k+=1
        if done<0:
            done=min(k,n-1); acc+=rem*(((hb[done]+lb[done])/2-ep) if s>0 else (ep-(ha[done]+la[done])/2))
        et[N]=j;xt[N]=done;pnl[N]=acc;sd[N]=s;N+=1
        i=done+1
    return et[:N],xt[:N],pnl[:N],sd[:N]
A=dict(ob=m5.ob.values,oa=m5.oa.values,hb=m5.hb.values,lb=m5.lb.values,ha=m5.ha.values,la=m5.la.values)
def run(sig):
    e,x,p,s=sim(sig,A['ob'],A['oa'],A['hb'],A['lb'],A['ha'],A['la'],15.0,18.75,37.50,56.25,0.02)
    gp=p[p>0].sum(); gl=-p[p<0].sum()
    return len(p),(p>0).mean()*100,gp/max(gl,1e-9),p.sum(),p.mean()/(p.std()/np.sqrt(len(p)))
print("="*112)
print(f"{'Skenario':44s} {'n':>6s} {'WR%':>7s} {'PF':>7s} {'net USD/oz':>12s} {'t':>7s}")
print("="*112)
sc=mk(BSL,SSL); r=run(sc); print(f"{'ICAS sinyal asli (level KAUSAL)':44s} {r[0]:6d} {r[1]:7.2f} {r[2]:7.4f} {r[3]:+12.1f} {r[4]:+7.2f}")
sl_=mk(BSL_L,SSL_L); r2=run(sl_); print(f"{'ICAS dgn level BOCOR (replika bug F-18)':44s} {r2[0]:6d} {r2[1]:7.2f} {r2[2]:7.4f} {r2[3]:+12.1f} {r2[4]:+7.2f}")
print(f"{'   -> selisih akibat kebocoran':44s} {'':6s} {r2[1]-r[1]:+7.2f} {r2[2]-r[2]:+7.4f} {r2[3]-r[3]:+12.1f}")
print("-"*112)
rng=np.random.default_rng(11); nsig=int((sc!=0).sum())
pfs=[]
for k in range(8):
    rs=np.zeros(len(sc),np.int64)
    idx=rng.choice(len(sc)-10,nsig,replace=False)
    rs[idx]=rng.choice(np.array([-1,1]),nsig)
    r3=run(rs); pfs.append(r3[2])
    if k<3: print(f"{'ACAK #'+str(k+1)+' (geometri SL/TP identik)':44s} {r3[0]:6d} {r3[1]:7.2f} {r3[2]:7.4f} {r3[3]:+12.1f} {r3[4]:+7.2f}")
print(f"{'ACAK rata-rata 8 seed':44s} {'':6s} {'':7s} {np.mean(pfs):7.4f}")
print("="*112)
print(f"VONIS: PF sinyal ICAS {r[2]:.4f} vs PF entry acak {np.mean(pfs):.4f}  ->  selisih {r[2]-np.mean(pfs):+.4f}")
