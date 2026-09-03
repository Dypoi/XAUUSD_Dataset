import pandas as pd, numpy as np, glob, os
files=sorted(glob.glob('/home/user/XAUUSD_Dataset/XAUUSD_M1_*.csv'))
out='/home/user/XAUUSD_Dataset/research/m1.parquet'
if not os.path.exists(out):
    dfs=[pd.read_csv(f,parse_dates=['timestamp']) for f in files]
    df=pd.concat(dfs,ignore_index=True)
    df=df.sort_values('timestamp').drop_duplicates('timestamp')
    df.to_parquet(out)
else:
    df=pd.read_parquet(out)
print(df.shape, df.timestamp.min(), df.timestamp.max())
print(df.isna().sum().sum(),"nan")
sp=(df.close_ask-df.close_bid)
print("spread stats(usd):", sp.describe([.01,.5,.9,.99]).to_dict())
bad=((df.high_bid<df.low_bid)|(df.close_bid>df.high_bid)|(df.close_bid<df.low_bid)|(df.close_ask>df.high_ask)|(df.close_ask<df.low_ask)|(sp<0)).sum()
print("bad OHLC rows:",bad)
d=df.set_index('timestamp')
print("bars per weekday:", d.groupby(d.index.dayofweek).size().to_dict())
print("bars per hour sample:", d.groupby(d.index.hour).size().to_dict())
gaps=d.index.to_series().diff().dt.total_seconds().div(60)
print("gap>5min count:",(gaps>5).sum(), "max gap min:",gaps.max())
print("yearly rows:", d.groupby(d.index.year).size().to_dict())
mid=(d.close_bid+d.close_ask)/2
print("price range:",mid.min(),mid.max())
r=np.log(mid).diff()
print("m1 ret std bps:", r.std()*1e4, "kurt:",r.kurtosis())
