"""KONTROL: apakah 'edge' setup ICT di H1 nyata, atau cuma drift long emas?"""
import pandas as pd, numpy as np
d=pd.read_parquet('m1.parquet').set_index('timestamp').sort_index()
mid=(d.close_bid+d.close_ask)/2
b=pd.DataFrame({'o':mid.resample('1h').first(),'h':mid.resample('1h').max(),
  'l':mid.resample('1h').min(),'c':mid.resample('1h').last()}).dropna()
lg=np.log(b.c); COST=3.6
f48=(lg.shift(-48)-lg)*1e4

print("="*118)
print("BASELINE: LONG ACAK, hold 48 jam (tanpa setup apa pun)")
print("="*118)
rng=np.random.default_rng(1)
for n in (2500,5500,9000):
    m=pd.Series(False,index=b.index); m.iloc[rng.choice(len(b)-48,n,replace=False)]=True
    x=f48[m].dropna()
    print(f"  long acak n={n:5d}: gross={x.mean():+6.2f} net={x.mean()-COST:+6.2f} t={x.mean()/(x.std()/np.sqrt(len(x))):+5.2f}")
allx=f48.dropna()
print(f"  SEMUA bar (drift pasif) : gross={allx.mean():+6.2f} net={allx.mean()-COST:+6.2f}")
print("\n  -> Emas naik ~+9 bps per 48 jam TANPA setup apa pun. Ini benchmark sesungguhnya.\n")

print("="*118)
print("EXCESS RETURN: setup ICT dikurangi baseline drift (+8.98 bps)")
print("="*118)
base=allx.mean()
def swings(b,n=5):
    sh=(b.h==b.h.rolling(2*n+1,center=True).max()).shift(n).fillna(False)
    sl=(b.l==b.l.rolling(2*n+1,center=True).min()).shift(n).fillna(False)
    return sh,sl
sh,sl=swings(b)
lsh=b.h.where(sh).ffill(); lsl=b.l.where(sl).ffill()
atr=(b.h-b.l).rolling(48).mean(); rngv=lsh-lsl; fib=(b.c-lsl)/rngv
setups={
 "BOS bullish -> long":((b.c>lsh)&(b.c.shift(1)<=lsh),1),
 "Turtle Soup low -> long":((b.l<lsl)&(b.c>lsl),1),
 "OTE long (retrace)":((fib>0.21)&(fib<0.38)&(rngv>0.5*atr),1),
 "Discount zone -> long":((fib<0.5)&(rngv>0.5*atr),1),
}
rows=[]
for nm,(m,s) in setups.items():
    x=(s*f48[m.fillna(False)]).dropna()
    exc=x.mean()-base
    t_exc=exc/(x.std()/np.sqrt(len(x)))
    rows.append((nm,len(x),x.mean(),x.mean()-COST,exc,t_exc))
    print(f"{nm:28s} n={len(x):6d} gross={x.mean():+6.2f} net={x.mean()-COST:+6.2f} | "
          f"EXCESS vs drift={exc:+6.2f} (t={t_exc:+5.2f}) {'<- kalah drift' if exc<0 else ''}")

print("\n" + "="*118)
print("UJI PALING JUJUR: setup ICT vs BUY & HOLD pasif, basis tahunan")
print("="*118)
m=((b.l<lsl)&(b.c>lsl)).fillna(False)   # Turtle Soup long = yg terbaik
x=(f48[m]).dropna()
yr_setup=x.groupby(x.index.year).mean()
yr_base=allx.groupby(allx.index.year).mean()
cmp=pd.DataFrame({'setup_gross':yr_setup.round(2),'drift_pasif':yr_base.round(2)})
cmp['excess']=(cmp.setup_gross-cmp.drift_pasif).round(2)
cmp['setup_menang']=cmp.excess>0
print(cmp.to_string())
print(f"\nTahun setup mengalahkan drift pasif: {int(cmp.setup_menang.sum())}/{len(cmp)}")
