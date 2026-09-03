import pandas as pd,numpy as np,lab
b=lab.make('4h'); BPY=6*252
c=np.log(b.c); vol=b.ret.rolling(500).std()
def z(n): return (c-c.shift(n))/(vol*np.sqrt(n))
cands={
 'trend_ens':(np.tanh(z(120))+np.tanh(z(240))+np.tanh(z(720)))/3,
 'trend_ens_longonly':((np.tanh(z(120))+np.tanh(z(240))+np.tanh(z(720)))/3).clip(0,None),
 'longbias':0.5+0.5*(np.tanh(z(120))+np.tanh(z(240))+np.tanh(z(720)))/3,
 'buyhold':pd.Series(1.0,index=b.index),
}
splits=[('2016-09','2021-08','IS'),('2021-09','2026-09','OOS')]
for name,p in cands.items():
    line=[f"{name:20s}"]
    for a,bb,tag in splits:
        sub=b.loc[a:bb]; ps=p.loc[a:bb].fillna(0)
        r=lab.evaluate(sub,ps,BPY,vol_target=0.10,cap=3,name=name)
        line.append(f"{tag}: Sh={r['sharpe']:+.2f} CAGR={r['cagr']:+.1f}% DD={r['maxdd']:.1f}%")
    print("  ".join(line))
