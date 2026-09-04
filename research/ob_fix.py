"""Demonstrasi: kenapa backtest Order Block terlihat spektakuler = LOOK-AHEAD BIAS."""
import pandas as pd, numpy as np
d=pd.read_parquet('m1.parquet').set_index('timestamp').sort_index()
mid=(d.close_bid+d.close_ask)/2
sp=((d.close_ask-d.close_bid)/mid*1e4)
b=pd.DataFrame({'o':mid.resample('15min').first(),'h':mid.resample('15min').max(),
  'l':mid.resample('15min').min(),'c':mid.resample('15min').last()}).dropna()
lg=np.log(b.c); atr=(b.h-b.l).rolling(48).mean()
COST=3.6

def rep(name,mask,sign):
    m=mask.fillna(False); n=m.sum()
    o=[f"{name:46s} n={n:6d}"]
    for k in (6,12,24):
        f=(lg.shift(-k)-lg)*1e4
        x=(sign*f[m]).dropna()
        if len(x)<50: continue
        o.append(f"h{k}: gross{x.mean():+7.2f} net{x.mean()-COST:+7.2f} (t{x.mean()/(x.std()/np.sqrt(len(x))):+6.1f})")
    print("  ".join(o))

print("### VERSI SALAH (pakai shift(-3) = melihat masa depan saat MENDEFINISIKAN OB)")
imp_up=(b.c.shift(-3)-b.c)>1.5*atr
obl=b.l.where((b.c<b.o)&imp_up).ffill(limit=40)
rep("Retest Bullish OB -> LONG  [BOCOR]",(b.l<=obl)&(b.l.shift(1)>obl)&obl.notna(),1)
rep("Retest Bullish OB -> SHORT [BOCOR]",(b.l<=obl)&(b.l.shift(1)>obl)&obl.notna(),-1)
print("  ^ long DAN short dua-duanya profit besar = mustahil = bukti kebocoran\n")

print("### VERSI BENAR (impulse dikonfirmasi 3 bar SEBELUM sinyal, semua kausal)")
# OB terkonfirmasi pada bar i: impulse terjadi di bar i-3..i, OB = bar bearish di i-3
imp_up_c=(b.c-b.c.shift(3))>1.5*atr          # impulse SUDAH terjadi (kausal)
ob_bar=(b.c.shift(3)<b.o.shift(3))            # bar bearish terakhir sblm impulse
obl2=b.l.shift(3).where(imp_up_c&ob_bar).shift(1).ffill(limit=40)  # +shift(1) baru bisa dipakai
rep("Retest Bullish OB -> LONG  [KAUSAL]",(b.l<=obl2)&(b.l.shift(1)>obl2)&obl2.notna(),1)
imp_dn_c=(b.c.shift(3)-b.c)>1.5*atr
ob_bar2=(b.c.shift(3)>b.o.shift(3))
obh2=b.h.shift(3).where(imp_dn_c&ob_bar2).shift(1).ffill(limit=40)
rep("Retest Bearish OB -> SHORT [KAUSAL]",(b.h>=obh2)&(b.h.shift(1)<obh2)&obh2.notna(),-1)

print("\n### KONTROL: zona ACAK dengan mekanisme retest yang sama")
rng=np.random.default_rng(7)
rand_zone=b.l.where(pd.Series(rng.random(len(b))<0.02,index=b.index)).shift(1).ffill(limit=40)
rep("Retest zona ACAK -> LONG",(b.l<=rand_zone)&(b.l.shift(1)>rand_zone)&rand_zone.notna(),1)
