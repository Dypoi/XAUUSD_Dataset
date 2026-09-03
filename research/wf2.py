import pandas as pd,numpy as np,lab
b=lab.make('4h'); BPY=6*252
c=np.log(b.c); vol=b.ret.rolling(500).std()
def z(n): return (c-c.shift(n))/(vol*np.sqrt(n))
ens=(np.tanh(z(120))+np.tanh(z(240))+np.tanh(z(720)))/3
cands={
 'buyhold':pd.Series(1.0,index=b.index),
 'crashfilter':(ens>-0.35).astype(float),
 'crashfilter2':(z(240)>-1.0).astype(float),
 'ladder':(0.4+0.6*((ens>0).astype(float))),
 'ladder2':(0.25+0.75*((ens>-0.2).astype(float))),
 'longbias':0.5+0.5*ens,
}
splits=[('2016-09','2021-08','IS'),('2021-09','2026-09','OOS'),('2016-09','2026-09','FULL')]
for name,p in cands.items():
    line=[f"{name:14s}"]
    for a,bb,tag in splits:
        r=lab.evaluate(b.loc[a:bb],p.loc[a:bb].fillna(0),BPY,vol_target=0.10,cap=3)
        line.append(f"{tag} Sh={r['sharpe']:+.2f} CAGR={r['cagr']:+.1f} DD={r['maxdd']:.1f} Cal={r['calmar']:.2f}")
    print(" | ".join(line))
