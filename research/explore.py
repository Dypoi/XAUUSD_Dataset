import pandas as pd, numpy as np
d=pd.read_parquet('/home/user/XAUUSD_Dataset/research/m1.parquet').set_index('timestamp')
mid=(d.close_bid+d.close_ask)/2
m5=mid.resample('5min').last().dropna()
r=np.log(m5).diff()
# 1) autocorrelation of 5m returns overall and by hour
print("acf1 all:",r.autocorr(1),"acf2:",r.autocorr(2),"acf5:",r.autocorr(5))
h=r.groupby(r.index.hour)
print("\nhour: n, mean_bps, std_bps, acf1")
for hh,g in h:
    print(hh, len(g), round(g.mean()*1e4,3), round(g.std()*1e4,2), round(g.autocorr(1),4))
