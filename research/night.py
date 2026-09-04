import pandas as pd,numpy as np
d=pd.read_parquet('m1.parquet').set_index('timestamp').sort_index()
mid=(d.close_bid+d.close_ask)/2
oa=d.open_ask; ob=d.open_bid
def leg(h_in,hold,slip=0.02,comm=0.05):
    ent=d[(d.index.hour==h_in)&(d.index.minute==0)]
    ex=d.reindex(ent.index+pd.Timedelta(hours=hold))
    ok=(~ex.open_bid.isna()).values
    e=ent.open_ask.values[ok]+slip; x=ex.open_bid.values[ok]-slip
    return pd.DataFrame({'t':ent.index[ok],'e':e,'x':x,'pnl':x-e-comm}).set_index('t')
res={}
for h_in in (18,19,20,21):
  for hold in (2,3,4,5,6,8):
    r=leg(h_in,hold); rb=r.pnl/r.e*1e4
    res[(h_in,hold)]=(len(r),rb.mean(),rb.mean()/(rb.std()/np.sqrt(len(rb))),(rb>0).mean())
for k,v in sorted(res.items(),key=lambda kv:-kv[1][2])[:12]:
    print(k,"n=%d net=%.2fbps t=%.2f wr=%.3f"%v)
# best base = 20h/4h; add filters
base=leg(20,4)
mid_h=mid.resample('1h').last()
lg=np.log(mid_h)
def stat(mask,name,rb):
    x=rb[mask]
    if len(x)<100: return
    yr=x.groupby(x.index.year).mean().round(2)
    print(f"{name}: n={len(x)} net={x.mean():.2f}bps t={x.mean()/(x.std()/np.sqrt(len(x))):.2f} wr={(x>0).mean():.3f} pos_yrs={(yr>0).sum()}/{len(yr)}")
rb=(base.pnl/base.e*1e4)
sig200=(lg-lg.shift(200)).reindex(base.index)
mom20=(lg-lg.shift(20)).reindex(base.index)
day_ret=(lg-lg.shift(20)).reindex(base.index)   # ~ intraday move to 20:00
vol=lg.diff().rolling(500).std().reindex(base.index)
stat(pd.Series(True,index=base.index),"ALL",rb)
stat(sig200>0,"uptrend200h",rb); stat(sig200<0,"downtrend",rb)
stat(day_ret<0,"day down",rb); stat(day_ret>0,"day up",rb)
stat((day_ret/vol/np.sqrt(20))< -0.5,"day down z<-0.5",rb)
stat(base.index.dayofweek<4,"Mon-Thu",rb)
for dw in range(5):
    stat(base.index.dayofweek==dw,f"dow{dw}",rb)
