import pandas as pd,numpy as np
d=pd.read_parquet('m1.parquet').set_index('timestamp').sort_index()
mid=(d.close_bid+d.close_ask)/2
h=mid.resample('1h').last().dropna()
lg=np.log(h)
r=lg.diff()*1e4
seg={'asia 0-7':(0,7),'london 7-13':(7,13),'ny 13-20':(13,20),'late 20-24':(20,24)}
for k,(a,b) in seg.items():
    m=(r.index.hour>=a)&(r.index.hour<b)
    x=r[m]
    ann=x.sum()/10
    print(f"{k}: sum={x.sum():.0f}bps ann={ann/100:.2f}%/yr t={x.mean()/(x.std()/np.sqrt(len(x))):.2f}")
    yr=x.groupby(x.index.year).sum()/100
    print("   yearly %:",yr.round(1).to_dict())
