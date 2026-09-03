import pandas as pd, numpy as np
d=pd.read_parquet('/home/user/XAUUSD_Dataset/research/m1.parquet').set_index('timestamp')
mid=(d.close_bid+d.close_ask)/2
spb=((d.close_ask-d.close_bid)/mid*1e4)
print("spread bps by year:\n", spb.groupby(spb.index.year).median())
print("spread bps by hour:\n", spb.groupby(spb.index.hour).median().round(2).to_dict())
m5=pd.DataFrame({'o':mid.resample('5min').first(),'h':mid.resample('5min').max(),'l':mid.resample('5min').min(),'c':mid.resample('5min').last(),'sp':spb.resample('5min').median()}).dropna()
c=m5.c
z=(c-c.rolling(48).mean())/c.rolling(48).std()
hour=c.index.hour
fwd={k:(np.log(c).shift(-k)-np.log(c))*1e4 for k in (6,12,24,48)}
asia=(hour>=0)&(hour<7)
for th in (2,2.5,3,3.5):
    for lbl,sig,sgn in (("L",(z<-th)&asia,1),("S",(z>th)&asia,-1)):
        s=sig.fillna(False)
        row=[f"th{th}{lbl} n={s.sum():5d}"]
        for k,f in fwd.items():
            x=(sgn*f[s]).dropna()
            row.append(f"h{k}:{x.mean():+.2f}(t{x.mean()/(x.std()/np.sqrt(len(x))):.1f})")
        print(" ".join(row))
