"""Asian-range breakout screen (5m bars, mid) -> forward returns net of cost."""
import pandas as pd,numpy as np
d=pd.read_parquet('m1.parquet').set_index('timestamp').sort_index()
mid=(d.close_bid+d.close_ask)/2
m5=pd.DataFrame({'o':mid.resample('5min').first(),'h':mid.resample('5min').max(),
 'l':mid.resample('5min').min(),'c':mid.resample('5min').last()}).dropna()
day=m5.index.normalize(); hour=m5.index.hour
asia=(hour>=0)&(hour<7)
ah=m5.h.where(asia).groupby(day).transform('max')
al=m5.l.where(asia).groupby(day).transform('min')
# use only ranges finalized: valid after 07:00
rngu=ah.groupby(day).transform('last'); rngl=al.groupby(day).transform('last')
ah7=m5.h.where(asia).groupby(day).max().reindex(day).values
al7=m5.l.where(asia).groupby(day).min().reindex(day).values
ah7=pd.Series(ah7,index=m5.index); al7=pd.Series(al7,index=m5.index)
rng=ah7-al7
atrd=(m5.h-m5.l).rolling(288).mean()
win=(hour>=7)&(hour<13)
c=m5.c; lg=np.log(c)
fwd={k:(lg.shift(-k)-lg)*1e4 for k in (6,12,24,48,72)}
up=(c>ah7)&(c.shift(1)<=ah7)&win
dn=(c<al7)&(c.shift(1)>=al7)&win
for nm,s,sg in (('BO up',up,1),('BO dn',dn,-1)):
    for filt,fn in (('all',pd.Series(True,index=c.index)),('rng<1.2atr',rng<1.2*atrd*12),('rng>1.2atr',rng>1.2*atrd*12)):
        m=(s&fn).fillna(False)
        line=[f"{nm} {filt} n={m.sum():5d}"]
        for k,f in fwd.items():
            x=(sg*f[m]).dropna()
            if len(x)<50: continue
            line.append(f"h{k}:{x.mean():+.2f}(t{x.mean()/(x.std()/np.sqrt(len(x))):.1f})")
        print(" ".join(line))
