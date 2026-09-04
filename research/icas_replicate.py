"""
Replikasi INDEPENDEN strategi Model ICAS (Dypoi/jurnalicas) pada 10 TAHUN data.
Audit asli hanya menguji Jan-Jun 2026 (6 bulan). Ini uji out-of-sample 10x lebih panjang.

Aturan asli (src/strategy/icas_strategy.py):
  BUY : (low[-1]<=SSL or low[-2]<=SSL) and close>open and (close>swing_h[-6:-1] or bull_FVG)
  SELL: (high[-1]>=BSL or high[-2]>=BSL) and close<open and (close<swing_l[-6:-1] or bear_FVG)
  SSL = min(asian_low, london_low) ; BSL = max(asian_high, london_high)
  FVG bull: low > high[-2] + 0.30
  SL $15 | TP1 $18.75 (30%) | TP2 $37.50 (25%) | TP3 $56.25 (25%) | runner 20%
Level sesi dihitung KAUSAL (expanding max/min dalam hari berjalan) - bukan versi bocor.
"""
import pandas as pd, numpy as np
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
 'sp':(d.close_ask-d.close_bid).resample('5min').median(),
}).dropna()
day=m5.index.normalize(); hh=m5.index.hour

# --- LEVEL SESI KAUSAL (expanding, tidak bocor) ---
asia=(hh<7); lon=(hh>=7)&(hh<12)
g=m5.groupby(day)
ah=m5.h.where(asia).groupby(day).cummax().ffill()
al=m5.l.where(asia).groupby(day).cummin().ffill()
lh=m5.h.where(lon).groupby(day).cummax().ffill()
ll=m5.l.where(lon).groupby(day).cummin().ffill()
# reset tiap hari
ah=ah.groupby(day).ffill(); al=al.groupby(day).ffill()
BSL=pd.concat([ah,lh],axis=1).max(axis=1)
SSL=pd.concat([al,ll],axis=1).min(axis=1)

sw_h=m5.h.shift(2).rolling(5).max()   # high[idx-6:idx-1]
sw_l=m5.l.shift(2).rolling(5).min()
bull_fvg=m5.l>(m5.h.shift(2)+0.30)
bear_fvg=m5.h<(m5.l.shift(2)-0.30)
ssl_swept=(m5.l.shift(1)<=SSL)|(m5.l.shift(2)<=SSL)
bsl_swept=(m5.h.shift(1)>=BSL)|(m5.h.shift(2)>=BSL)
is_buy =ssl_swept&(m5.c>m5.o)&((m5.c>sw_h)|bull_fvg)
is_sell=bsl_swept&(m5.c<m5.o)&((m5.c<sw_l)|bear_fvg)
sig=np.where(is_buy.fillna(False),1,np.where(is_sell.fillna(False),-1,0)).astype(np.int64)

@njit(cache=True)
def sim(sig,ob,oa,hb,lb,ha,la,sl_d,tp1,tp2,tp3,slip):
    n=len(sig); N=0
    et=np.empty(n,np.int64); xt=np.empty(n,np.int64); pnl=np.empty(n); sd=np.empty(n,np.int64)
    i=0
    while i<n-1:
        s=sig[i]
        if s==0: i+=1; continue
        j=i+1
        if j>=n: break
        if s>0:
            ep=oa[j]+slip
            SL=ep-sl_d; T1=ep+tp1; T2=ep+tp2; T3=ep+tp3
        else:
            ep=ob[j]-slip
            SL=ep+sl_d; T1=ep-tp1; T2=ep-tp2; T3=ep-tp3
        rem=1.0; acc=0.0; k=j; done=-1
        h1=False;h2=False;h3=False
        while k<n and k<j+2000:
            if s>0:
                if lb[k]<=SL:
                    acc+=rem*((SL-slip)-ep); done=k; break
                if not h1 and hb[k]>=T1: acc+=0.30*(T1-ep); rem-=0.30; h1=True
                if not h2 and hb[k]>=T2: acc+=0.25*(T2-ep); rem-=0.25; h2=True
                if not h3 and hb[k]>=T3:
                    acc+=0.25*(T3-ep); rem-=0.25; h3=True; SL=T1  # step SL to TP1
            else:
                if ha[k]>=SL:
                    acc+=rem*(ep-(SL+slip)); done=k; break
                if not h1 and la[k]<=T1: acc+=0.30*(ep-T1); rem-=0.30; h1=True
                if not h2 and la[k]<=T2: acc+=0.25*(ep-T2); rem-=0.25; h2=True
                if not h3 and la[k]<=T3:
                    acc+=0.25*(ep-T3); rem-=0.25; h3=True; SL=T1
            if rem<=0.001: done=k; break
            k+=1
        if done<0:
            done=min(k,n-1)
            acc+=rem*(((hb[done]+lb[done])/2-ep) if s>0 else (ep-(ha[done]+la[done])/2))
        et[N]=j; xt[N]=done; pnl[N]=acc; sd[N]=s; N+=1
        i=done+1   # 1 posisi pada satu waktu
    return et[:N],xt[:N],pnl[:N],sd[:N]

et,xt,pnl,sd=sim(sig,m5.ob.values,m5.oa.values,m5.hb.values,m5.lb.values,
                 m5.ha.values,m5.la.values,15.0,18.75,37.50,56.25,0.02)
tr=pd.DataFrame({'t':m5.index[et],'exit':m5.index[xt],'usd_per_oz':pnl,'side':sd}).set_index('t')
print("="*104)
print("REPLIKASI MODEL ICAS — 10 TAHUN (2016-09..2026-09), level sesi KAUSAL")
print("="*104)
gp=tr.usd_per_oz[tr.usd_per_oz>0].sum(); gl=-tr.usd_per_oz[tr.usd_per_oz<0].sum()
print(f"Total trades : {len(tr):,}   ({len(tr)/10/252:.2f} per hari bursa)")
print(f"Win rate     : {(tr.usd_per_oz>0).mean()*100:.2f}%")
print(f"Profit Factor: {gp/gl:.4f}")
print(f"Net USD/oz   : {tr.usd_per_oz.sum():+,.2f}   (avg {tr.usd_per_oz.mean():+.4f}/trade)")
print(f"t-stat       : {tr.usd_per_oz.mean()/(tr.usd_per_oz.std()/np.sqrt(len(tr))):+.2f}")
print()
print("Per tahun:")
yr=tr.groupby(tr.index.year).usd_per_oz.agg(['count','sum','mean'])
yr['PF']=tr.groupby(tr.index.year).usd_per_oz.apply(lambda x: x[x>0].sum()/max(-x[x<0].sum(),1e-9))
yr['WR%']=tr.groupby(tr.index.year).usd_per_oz.apply(lambda x:(x>0).mean()*100)
print(yr.round(3).to_string())
print()
print("Per sisi:")
for s,nm in ((1,'BUY'),(-1,'SELL')):
    x=tr[tr.side==s].usd_per_oz
    p=x[x>0].sum()/max(-x[x<0].sum(),1e-9)
    print(f"  {nm}: n={len(x):6d} WR={100*(x>0).mean():.2f}% PF={p:.4f} net={x.sum():+,.1f} t={x.mean()/(x.std()/np.sqrt(len(x))):+.2f}")
tr.to_parquet('/home/user/XAUUSD_Dataset/reports/icas_trades_10y.parquet')
