"""Ronde 2: setup ICT/SMC yang belum diuji. SEMUA KAUSAL (no shift negatif)."""
import pandas as pd, numpy as np
d=pd.read_parquet('m1.parquet').set_index('timestamp').sort_index()
mid=(d.close_bid+d.close_ask)/2
sp=((d.close_ask-d.close_bid)/mid*1e4)
def bars(rule):
    return pd.DataFrame({'o':mid.resample(rule).first(),'h':mid.resample(rule).max(),
      'l':mid.resample(rule).min(),'c':mid.resample(rule).last()}).dropna()
COST=3.6

def rep(name,mask,sign,b,hz=(6,12,24,48)):
    lg=np.log(b.c); m=mask.fillna(False); n=int(m.sum())
    if n<100: print(f"{name:52s} n={n:6d}  (sampel kurang)"); return
    o=[f"{name:52s} n={n:6d}"]
    for k in hz:
        f=(lg.shift(-k)-lg)*1e4
        x=(sign*f[m]).dropna()
        o.append(f"h{k}:{x.mean():+6.2f}/net{x.mean()-COST:+6.2f}(t{x.mean()/(x.std()/np.sqrt(len(x))):+5.1f})")
    print("  ".join(o))

def swings(b,n=5):
    sh=(b.h==b.h.rolling(2*n+1,center=True).max())
    sl=(b.l==b.l.rolling(2*n+1,center=True).min())
    # KAUSAL: swing baru terkonfirmasi n bar setelahnya
    return sh.shift(n).fillna(False), sl.shift(n).fillna(False)

for tf in ('15min','1h'):
    b=bars(tf); print(f"\n{'='*140}\nTIMEFRAME {tf}\n{'='*140}")
    sh,sl=swings(b)
    last_sh=b.h.where(sh).ffill(); last_sl=b.l.where(sl).ffill()
    atr=(b.h-b.l).rolling(48).mean()

    # --- BOS / CHoCH ---
    bos_up=(b.c>last_sh)&(b.c.shift(1)<=last_sh)
    bos_dn=(b.c<last_sl)&(b.c.shift(1)>=last_sl)
    rep("BOS bullish -> long (continuation)",bos_up,1,b)
    rep("BOS bearish -> short (continuation)",bos_dn,-1,b)
    rep("CHoCH: BOS up -> FADE short",bos_up,-1,b)

    # --- Turtle Soup (false break swing) ---
    ts_long=(b.l<last_sl)&(b.c>last_sl)
    ts_short=(b.h>last_sh)&(b.c<last_sh)
    rep("Turtle Soup: false break LOW -> long",ts_long,1,b)
    rep("Turtle Soup: false break HIGH -> short",ts_short,-1,b)

    # --- OTE : retrace 0.62-0.79 dari leg terakhir ---
    rng=last_sh-last_sl
    fib=(b.c-last_sl)/rng
    ote_long=(fib>0.21)&(fib<0.38)&(rng>0.5*atr)&bos_up.rolling(20).max().astype(bool)
    ote_l2=(fib>0.21)&(fib<0.38)&(rng>0.5*atr)
    rep("OTE long (retrace 62-79% leg naik)",ote_l2,1,b)
    ote_s2=(fib>0.62)&(fib<0.79)&(rng>0.5*atr)
    rep("OTE short (retrace 62-79% leg turun)",ote_s2,-1,b)

    # --- Premium/Discount (equilibrium 50%) ---
    disc=(fib<0.5)&(rng>0.5*atr); prem=(fib>0.5)&(rng>0.5*atr)
    rep("Discount zone -> long",disc,1,b)
    rep("Premium zone -> short",prem,-1,b)

# --- Power of 3 / AMD : akumulasi Asia -> manipulasi -> distribusi ---
print(f"\n{'='*140}\nPOWER OF 3 (AMD) — arah candle harian vs manipulasi sesi\n{'='*140}")
b=bars('1h'); day=b.index.normalize()
o0=b.o.groupby(day).first()
asia_h=b.h[(b.index.hour<7)].groupby(day[b.index.hour<7]).max()
asia_l=b.l[(b.index.hour<7)].groupby(day[b.index.hour<7]).min()
# manipulasi London 7-11: mana yg disapu duluan
lon=b[(b.index.hour>=7)&(b.index.hour<11)]
lo_break=lon.l.groupby(lon.index.normalize()).min()<asia_l
hi_break=lon.h.groupby(lon.index.normalize()).max()>asia_h
# distribusi 11-20
dist=b[(b.index.hour>=11)&(b.index.hour<20)]
dr=(np.log(dist.c.groupby(dist.index.normalize()).last())-np.log(dist.o.groupby(dist.index.normalize()).first()))*1e4
for nm,mask,sgn in (("sweep LOW Asia pagi -> long siang",lo_break&~hi_break,1),
                    ("sweep HIGH Asia pagi -> short siang",hi_break&~lo_break,-1)):
    x=(sgn*dr[mask.reindex(dr.index).fillna(False)]).dropna()
    if len(x)<50: continue
    yr=x.groupby(x.index.year).mean()
    print(f"{nm:44s} n={len(x):5d} gross={x.mean():+6.2f} net={x.mean()-COST:+6.2f} "
          f"t={x.mean()/(x.std()/np.sqrt(len(x))):+5.2f} thn_positif={(yr>0).sum()}/{len(yr)}")
