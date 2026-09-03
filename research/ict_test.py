"""
Uji objektif primitif ICT/SMC pada XAUUSD M1 2016-2026.
Semua diuji dengan forward return NET (dikurangi spread aktual dataset).
"""
import pandas as pd, numpy as np
d=pd.read_parquet('m1.parquet').set_index('timestamp').sort_index()
mid=(d.close_bid+d.close_ask)/2
spread_bps=((d.close_ask-d.close_bid)/mid*1e4)

def bars(rule):
    b=pd.DataFrame({'o':mid.resample(rule).first(),'h':mid.resample(rule).max(),
      'l':mid.resample(rule).min(),'c':mid.resample(rule).last(),
      'sp':spread_bps.resample(rule).median()}).dropna()
    return b

m5=bars('5min'); m15=bars('15min')
COST=1.8*2  # round-turn approx bps (masuk ask, keluar bid)

def report(name,mask,sign,b,horizons=(6,12,24,48)):
    lg=np.log(b.c)
    m=mask.fillna(False)
    n=m.sum()
    if n<100: 
        print(f"{name}: n={n} (terlalu sedikit)"); return
    out=[f"{name:42s} n={n:6d}"]
    for k in horizons:
        f=(lg.shift(-k)-lg)*1e4
        x=(sign*f[m]).dropna()
        net=x.mean()-COST
        t=x.mean()/(x.std()/np.sqrt(len(x)))
        out.append(f"h{k}: gross{x.mean():+6.2f} net{net:+6.2f} (t{t:+5.1f})")
    print("  ".join(out))

print("="*130)
print("UJI 1: FAIR VALUE GAP (FVG) — apakah harga bereaksi saat mengisi imbalance?")
print("="*130)
# FVG bullish: low[i] > high[i-2]  -> gap antara high[i-2] dan low[i]
for b,tf in ((m5,'M5'),(m15,'M15')):
    h2=b.h.shift(2); l2=b.l.shift(2)
    bull_fvg = b.l > h2      # gap naik terbentuk di bar i
    bear_fvg = b.h < l2
    # ukuran gap relatif ATR
    atr=(b.h-b.l).rolling(48).mean()
    gap_up=(b.l-h2); gap_dn=(l2-b.h)
    big_up = bull_fvg & (gap_up>0.5*atr)
    big_dn = bear_fvg & (gap_dn>0.5*atr)
    report(f"{tf} FVG bullish terbentuk (cont. long)", big_up, 1, b)
    report(f"{tf} FVG bearish terbentuk (cont. short)", big_dn, -1, b)

print()
print("="*130)
print("UJI 2: LIQUIDITY SWEEP / JUDAS SWING — sapu high/low sesi Asia lalu reversal?")
print("="*130)
b=m5; lg=np.log(b.c)
day=b.index.normalize(); hour=b.index.hour
asia=(hour>=0)&(hour<7)
ah=b.h.where(asia).groupby(day).max().reindex(day); ah.index=b.index
al=b.l.where(asia).groupby(day).min().reindex(day); al.index=b.index
atr=(b.h-b.l).rolling(288).mean()
london=(hour>=7)&(hour<12)
ny=(hour>=12)&(hour<17)
for nm,win in (("London KZ 07-12",london),("NY KZ 12-17",ny)):
    # sweep high lalu close balik di bawah = bearish reversal
    swept_hi = (b.h>ah)&(b.c<ah)&win
    swept_lo = (b.l<al)&(b.c>al)&win
    report(f"Sweep Asian HIGH -> short  [{nm}]", swept_hi, -1, b)
    report(f"Sweep Asian LOW  -> long   [{nm}]", swept_lo, 1, b)

print()
print("="*130)
print("UJI 3: ORDER BLOCK — bar berlawanan terakhir sebelum impulse, reaksi saat retest?")
print("="*130)
b=m15; lg=np.log(b.c); atr=(b.h-b.l).rolling(48).mean()
ret=b.c.diff()
# bullish OB: bar bearish (c<o) diikuti impulse naik kuat >1.5 ATR dalam 3 bar
imp_up=(b.c.shift(-3)-b.c)>1.5*atr
bear_bar=b.c<b.o
ob_bull_zone=(bear_bar&imp_up)
# retest: harga kembali ke low bar OB dalam 20 bar berikutnya
obl=b.l.where(ob_bull_zone).ffill(limit=40)
retest_bull=(b.l<=obl)&(b.l.shift(1)>obl)&obl.notna()
report("Retest Bullish OB -> long", retest_bull, 1, b)
imp_dn=(b.c-b.c.shift(-3))>1.5*atr
bull_bar=b.c>b.o
ob_bear=(bull_bar&imp_dn)
obh=b.h.where(ob_bear).ffill(limit=40)
retest_bear=(b.h>=obh)&(b.h.shift(1)<obh)&obh.notna()
report("Retest Bearish OB -> short", retest_bear, -1, b)

print()
print("="*130)
print("UJI 4: KILLZONE — apakah jam ICT benar-benar punya edge arah?")
print("="*130)
h1=bars('1h'); r1=(np.log(h1.c).diff()*1e4)
kz={'London KZ 07-10':(7,10),'NY AM KZ 12-15':(12,15),'London Close 15-17':(15,17),
    'Asian KZ 00-03':(0,3),'Silver Bullet 14-15':(14,15)}
for k,(a,bb) in kz.items():
    x=r1[(r1.index.hour>=a)&(r1.index.hour<bb)]
    yr=x.groupby(x.index.year).sum()/100
    print(f"{k:24s} mean={x.mean():+6.3f}bps/jam  t={x.mean()/(x.std()/np.sqrt(len(x))):+5.2f}  "
          f"ann={x.sum()/10/100:+6.2f}%  tahun_positif={(yr>0).sum()}/{len(yr)}")
