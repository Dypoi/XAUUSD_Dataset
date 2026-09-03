import pandas as pd,numpy as np
d=pd.read_parquet('m1.parquet').set_index('timestamp')
mid=(d.close_bid+d.close_ask)/2
h1=mid.resample('1h').last().dropna()
# window drift: enter at hour A open, exit at hour B
for a,b in [(20,24),(21,24),(22,24),(23,24),(20,2),(22,2),(23,3),(0,2),(6,9),(13,16)]:
    # build daily
    df=pd.DataFrame({'p':mid})
    ent=mid.resample('1h').first()
    entp=ent[ent.index.hour==a]
    if b>a and b<=23: exp=ent[ent.index.hour==b]
    else: exp=None
    # generic: exit b hours later
    hold=(b-a)%24
    ex=entp.index+pd.Timedelta(hours=hold)
    exv=ent.reindex(ex)
    r=(np.log(exv.values)-np.log(entp.values))*1e4
    r=pd.Series(r,index=entp.index).dropna()
    yr=r.groupby(r.index.year).mean().round(2)
    print(f"{a}->{b} hold{hold}h n={len(r)} mean={r.mean():.2f}bps t={r.mean()/(r.std()/np.sqrt(len(r))):.2f} yearly={list(yr.values)}")
