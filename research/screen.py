import pandas as pd, numpy as np
d=pd.read_parquet('/home/user/XAUUSD_Dataset/research/m1.parquet').set_index('timestamp')
mid=(d.close_bid+d.close_ask)/2
m5=pd.DataFrame({'o':mid.resample('5min').first(),'h':mid.resample('5min').max(),'l':mid.resample('5min').min(),'c':mid.resample('5min').last()}).dropna()
c=m5.c; r=np.log(c).diff()
atr=(m5.h-m5.l).rolling(48).mean()
z=(c-c.rolling(48).mean())/c.rolling(48).std()
fwd={k: (np.log(c).shift(-k)-np.log(c))*1e4 for k in (3,6,12,24)}
hour=c.index.hour
def rep(name,sig):
    s=sig.fillna(False)
    print(f"\n{name}: n={s.sum()}")
    for k,f in fwd.items():
        x=f[s]
        print(f"  h{k}: mean={x.mean():.2f}bps med={x.median():.2f} t={x.mean()/ (x.std()/np.sqrt(len(x))):.1f} hit={np.mean(x>0):.3f}")
# momentum/breakout
hh=m5.h.rolling(24).max().shift(1); ll=m5.l.rolling(24).min().shift(1)
rep("break_up_2h", (c>hh))
rep("break_dn_2h", -(c<ll)*1 == -1)  # placeholder
# proper: short signal -> use negative fwd
def reps(name,sig,sign):
    s=sig.fillna(False)
    print(f"\n{name}: n={s.sum()}")
    for k,f in fwd.items():
        x=sign*f[s]
        print(f"  h{k}: mean={x.mean():.2f}bps t={x.mean()/(x.std()/np.sqrt(max(len(x),1))):.1f} hit={np.mean(x>0):.3f}")
reps("break_dn_2h",(c<ll),-1)
# session filter London/NY
sess=(hour>=7)&(hour<16)
reps("break_up_2h_LN",(c>hh)&sess,1); reps("break_dn_2h_LN",(c<ll)&sess,-1)
# mean reversion z
reps("z<-2 long",(z<-2),1); reps("z>2 short",(z>2),-1)
asia=(hour>=0)&(hour<7)
reps("z<-2 long asia",(z<-2)&asia,1); reps("z>2 short asia",(z>2)&asia,-1)
# big 5m spike fade
sp=r/ (r.rolling(288).std())
reps("spike<-3 fade long",(sp<-3),1); reps("spike>3 fade short",(sp>3),-1)
reps("spike<-3 cont short",(sp<-3),-1)
