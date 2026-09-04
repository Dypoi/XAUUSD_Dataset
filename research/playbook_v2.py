"""
BACKTEST PLAYBOOK v2 — 3 perbaikan diterapkan.
V1 = kodifikasi playbook asli (= logika ICAS: sweep -> fade/reversal)
V2 = V1 + (1) Judas dibalik jadi continuation
          (2) long-only kecuali bias D/H4 bearish
          (3) tanpa gerbang killzone
Aturan risiko playbook: risk $80/trade (0.4% dari 20k -> di sini 0.8% dari 10k),
maks 2 trade/hari, stop rugi harian, stop profit harian, 2 kalah beruntun -> stop.
SL dari CISD M5 = 80-150 pips ($8-15). RR 1:2 (partial 50% di 1R, sisa ke 2R).
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

# --- level sesi KAUSAL ---
asia=(hh<7); lon=(hh>=7)&(hh<12)
ah=m5.h.where(asia).groupby(day).cummax().ffill(); al=m5.l.where(asia).groupby(day).cummin().ffill()
lh=m5.h.where(lon).groupby(day).cummax().ffill(); ll=m5.l.where(lon).groupby(day).cummin().ffill()
BSL=pd.concat([ah,lh],axis=1).max(axis=1); SSL=pd.concat([al,ll],axis=1).min(axis=1)

sw_h=m5.h.shift(2).rolling(5).max(); sw_l=m5.l.shift(2).rolling(5).min()
bfvg=m5.l>(m5.h.shift(2)+0.30); sfvg=m5.h<(m5.l.shift(2)-0.30)
ssl_swept=(m5.l.shift(1)<=SSL)|(m5.l.shift(2)<=SSL)
bsl_swept=(m5.h.shift(1)>=BSL)|(m5.h.shift(2)>=BSL)

# CISD/displacement
bull_disp=(m5.c>m5.o)&((m5.c>sw_h)|bfvg)
bear_disp=(m5.c<m5.o)&((m5.c<sw_l)|sfvg)

# ---- BIAS MAKRO D/H4 (aturan objektif pengganti "bias External") ----
h4=m5.c.resample('4h').last().dropna()
ma240=h4.rolling(240).mean()          # ~40 hari
bias_bull=(h4>ma240).reindex(m5.index,method='ffill')
bias_bear=(h4<ma240).reindex(m5.index,method='ffill')

# ---- KILLZONE (untuk perbandingan) : London 06-09 UTC, NY 11-14 UTC ----
kz=((hh>=6)&(hh<9))|((hh>=11)&(hh<14))

# ================== DEFINISI SINYAL ==================
# V1 ASLI: sweep SSL -> BUY (fade) ; sweep BSL -> SELL (fade)
v1_buy = ssl_swept & bull_disp
v1_sell= bsl_swept & bear_disp

# V2 FIX-1 (Judas DIBALIK = continuation):
#   sweep SSL lalu displacement BEARISH -> SELL (lanjut turun)
#   sweep BSL lalu displacement BULLISH -> BUY  (lanjut naik)
v2_buy_raw = bsl_swept & bull_disp
v2_sell_raw= ssl_swept & bear_disp
# FIX-2: long-only kecuali bias bearish
v2_buy = v2_buy_raw & bias_bull
v2_sell= v2_sell_raw & bias_bear
# FIX-3: tanpa killzone (default). Varian dengan killzone utk bandingkan.

def mksig(b,s):
    return np.where(b.fillna(False),1,np.where(s.fillna(False),-1,0)).astype(np.int64)

@njit(cache=True)
def sim(sig,ob,oa,hb,lb,ha,la,dayid,sl_usd,rr,risk_usd,eq0,
        max_trades_day,daily_loss_lim,daily_profit_lim,max_consec_loss,slip):
    n=len(sig)
    eq=eq0
    et=np.empty(n,np.int64);xt=np.empty(n,np.int64);pnl=np.empty(n)
    sd=np.empty(n,np.int64);eqa=np.empty(n);lots=np.empty(n)
    N=0; i=0
    cur_day=-1; ntoday=0; pnl_today=0.0; consec=0
    while i<n-1:
        if dayid[i]!=cur_day:
            cur_day=dayid[i]; ntoday=0; pnl_today=0.0; consec=0
        s=sig[i]
        if s==0: i+=1; continue
        if ntoday>=max_trades_day: i+=1; continue
        if pnl_today<=-daily_loss_lim: i+=1; continue
        if pnl_today>=daily_profit_lim: i+=1; continue
        if consec>=max_consec_loss: i+=1; continue
        if eq<=0: break
        j=i+1
        spread=oa[j]-ob[j]
        sl_eff=sl_usd+spread+slip
        lot=risk_usd/(sl_eff*100.0)      # 1 lot = 100 oz
        if lot<0.01: lot=0.01
        if lot>50.0: lot=50.0
        if s>0:
            ep=oa[j]+slip; SL=ep-sl_usd; T1=ep+sl_usd; T2=ep+rr*sl_usd
        else:
            ep=ob[j]-slip; SL=ep+sl_usd; T1=ep-sl_usd; T2=ep-rr*sl_usd
        rem=1.0; acc=0.0; k=j; done=-1; hit1=False
        while k<n and k<j+3000:
            if s>0:
                if lb[k]<=SL: acc+=rem*((SL-slip)-ep); done=k; break
                if not hit1 and hb[k]>=T1:
                    acc+=0.5*(T1-ep); rem=0.5; hit1=True; SL=ep+spread  # BE+
                if hit1 and hb[k]>=T2: acc+=rem*(T2-ep); rem=0.0; done=k; break
            else:
                if ha[k]>=SL: acc+=rem*(ep-(SL+slip)); done=k; break
                if not hit1 and la[k]<=T1:
                    acc+=0.5*(ep-T1); rem=0.5; hit1=True; SL=ep-spread
                if hit1 and la[k]<=T2: acc+=rem*(ep-T2); rem=0.0; done=k; break
            k+=1
        if done<0:
            done=min(k,n-1)
            mp=(hb[done]+lb[done])/2 if s>0 else (ha[done]+la[done])/2
            acc+=rem*((mp-ep) if s>0 else (ep-mp))
        usd=acc*lot*100.0
        eq+=usd; pnl_today+=usd; ntoday+=1
        consec = consec+1 if usd<0 else 0
        et[N]=j; xt[N]=done; pnl[N]=usd; sd[N]=s; eqa[N]=eq; lots[N]=lot; N+=1
        i=done+1
    return et[:N],xt[:N],pnl[:N],sd[:N],eqa[:N],lots[:N]

dayid=np.asarray(day.view('int64')//86_400_000_000, dtype=np.int64)
A=[m5.ob.values,m5.oa.values,m5.hb.values,m5.lb.values,m5.ha.values,m5.la.values,dayid]

def run(sig,sl_usd=12.0,rr=2.0,risk=80.0,eq0=10000.0,maxday=2,dl=250.0,dp=400.0,mcl=2,slip=0.02):
    e,x,p,s,eq,lot=sim(sig,*A,sl_usd,rr,risk,eq0,maxday,dl,dp,mcl,slip)
    if len(p)==0: return None
    tr=pd.DataFrame({'t':m5.index[e],'exit':m5.index[x],'usd':p,'side':s,'eq':eq,'lot':lot}).set_index('t')
    gp=p[p>0].sum(); gl=-p[p<0].sum()
    ec=pd.Series(eq,index=tr.index)
    dd=(ec/ec.cummax()-1)
    yrs=(tr.index[-1]-tr.index[0]).days/365.25
    ndays=len(np.unique(tr.index.normalize()))
    return dict(tr=tr,n=len(p),wr=(p>0).mean()*100,pf=gp/max(gl,1e-9),net=p.sum(),
        final=eq[-1],dd=dd.min()*100,yrs=yrs,
        cagr=((eq[-1]/eq0)**(1/yrs)-1)*100 if eq[-1]>0 else -100,
        perday=len(p)/ (10*252), perday_active=len(p)/max(ndays,1),
        active_days=ndays, avg_win=p[p>0].mean() if (p>0).any() else 0,
        avg_loss=p[p<0].mean() if (p<0).any() else 0, eqser=ec)

print("="*126)
print("BACKTEST — PLAYBOOK v1 (asli) vs v2 (3 perbaikan). Balance $10,000 | risk $80/trade | maks 2 trade/hari | SL $12 | RR 1:2")
print("="*126)
print(f"{'Konfigurasi':52s} {'n':>6s} {'WR%':>6s} {'PF':>6s} {'Net$':>10s} {'Final$':>10s} {'DD%':>7s} {'/hari':>6s}")
print("-"*126)
cfgs=[
 ("V1 ASLI (fade sweep, 2 arah, tanpa KZ)", mksig(v1_buy,v1_sell)),
 ("V1 ASLI + gerbang killzone",             mksig(v1_buy&kz,v1_sell&kz)),
 ("V2 fix1 saja (Judas dibalik, 2 arah)",   mksig(v2_buy_raw,v2_sell_raw)),
 ("V2 fix1+2 (dibalik + bias D/H4)",        mksig(v2_buy,v2_sell)),
 ("V2 fix1+2+3 LENGKAP (tanpa KZ)",         mksig(v2_buy,v2_sell)),
 ("V2 LENGKAP + gerbang killzone (dibanding)",mksig(v2_buy&kz,v2_sell&kz)),
 ("V2 LONG-ONLY murni (SELL dimatikan)",    mksig(v2_buy,pd.Series(False,index=m5.index))),
]
res={}
for nm,sg in cfgs:
    r=run(sg); res[nm]=r
    if r is None: print(f"{nm:52s}  -- tidak ada trade --"); continue
    print(f"{nm:52s} {r['n']:6d} {r['wr']:6.2f} {r['pf']:6.3f} {r['net']:+10.0f} {r['final']:10.0f} {r['dd']:7.1f} {r['perday']:6.2f}")
import pickle; pickle.dump({k:(v['tr'] if v else None) for k,v in res.items()},open('/tmp/pbv2.pkl','wb'))
