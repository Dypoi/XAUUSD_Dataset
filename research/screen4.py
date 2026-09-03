import pandas as pd,numpy as np
d=pd.read_parquet('m1.parquet').set_index('timestamp')
mid=(d.close_bid+d.close_ask)/2
def bars(rule):
    return pd.DataFrame({'o':mid.resample(rule).first(),'h':mid.resample(rule).max(),
        'l':mid.resample(rule).min(),'c':mid.resample(rule).last()}).dropna()
for rule,horizons in (('15min',(4,8,16,32)),('1h',(2,4,8,24))):
    b=bars(rule); c=b.c; lg=np.log(c)
    atr=(b.h-b.l).rolling(20).mean()
    fwd={k:(lg.shift(-k)-lg)*1e4 for k in horizons}
    feats={}
    for n in (12,24,48,96):
        feats[f'mom{n}']=(lg-lg.shift(n))/ (lg.diff().rolling(n*3).std()*np.sqrt(n))
    feats['rng']=(c-b.l.rolling(48).min())/(b.h.rolling(48).max()-b.l.rolling(48).min())-0.5
    feats['vol']=np.log(atr/atr.rolling(200).mean())
    print(f"=== {rule} : IC (spearman) of feature vs fwd ret")
    for fn,f in feats.items():
        line=[fn]
        for k,fw in fwd.items():
            x=pd.concat([f,fw],axis=1).dropna()
            ic=x.iloc[:,0].corr(x.iloc[:,1],method='spearman')
            line.append(f"h{k}:{ic:+.4f}")
        print("  ",*line)
