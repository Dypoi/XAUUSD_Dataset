import pandas as pd,numpy as np
d=pd.read_parquet('m1.parquet').set_index('timestamp').sort_index()
def leg(h_in,hold,slip=0.02,comm=0.05):
    ent=d[(d.index.hour==h_in)&(d.index.minute==0)]
    ex=d.reindex(ent.index+pd.Timedelta(hours=hold))
    ok=(~ex.open_bid.isna()).values
    e=ent.open_ask.values[ok]+slip; x=ex.open_bid.values[ok]-slip
    return pd.DataFrame({'t':ent.index[ok],'e':e,'pnl':x-e-comm}).set_index('t')
rows=[]
for h in range(0,24):
  for hold in (1,2,3,4,5,6,7,8):
    r=leg(h,hold)
    if len(r)<500: continue
    rb=r.pnl/r.e*1e4
    yr=rb.groupby(rb.index.year).mean()
    rows.append((h,hold,len(r),round(rb.mean(),2),round(rb.mean()/(rb.std()/np.sqrt(len(rb))),2),int((yr>0).sum()),len(yr)))
df=pd.DataFrame(rows,columns=['h_in','hold','n','net_bps','t','pos_yrs','yrs'])
print(df.sort_values('t',ascending=False).head(20).to_string(index=False))
