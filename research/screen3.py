import pandas as pd, numpy as np
d=pd.read_parquet('/home/user/XAUUSD_Dataset/research/m1.parquet').set_index('timestamp')
mid=(d.close_bid+d.close_ask)/2
h1=mid.resample('1h').last().dropna()
r=(np.log(h1).diff()*1e4)
tab=r.groupby([r.index.year,r.index.hour]).mean().unstack().round(2)
print("mean bps per hour by year"); print(tab.to_string())
print("\nfull-sample hour mean/t:")
g=r.groupby(r.index.hour)
print(pd.DataFrame({'mean':g.mean(),'t':g.mean()/(g.std()/np.sqrt(g.count())),'n':g.count()}).round(2).to_string())
# Asian range breakout
