import pandas as pd,numpy as np
d=pd.read_parquet('m1.parquet').set_index('timestamp').sort_index()
oa=d.open_ask; ob=d.open_bid
mid=(d.close_bid+d.close_ask)/2
def sess_long(h_in,h_out,slip=0.02,comm=0.10):
    ent=d[(d.index.hour==h_in)&(d.index.minute==0)]
    hold=(h_out-h_in)%24
    ex_ts=ent.index+pd.Timedelta(hours=hold)
    ex=d.reindex(ex_ts)
    ok=~ex.open_bid.isna()
    e=ent.open_ask.values[ok.values]+slip
    x=ex.open_bid.values[ok.values]-slip
    pnl=x-e-comm
    t=ent.index[ok.values]
    return pd.DataFrame({'t':t,'entry':e,'exit':x,'pnl':pnl,'ret_bps':pnl/e*1e4})
for a,b in [(20,2),(20,0),(23,3),(21,0)]:
    r=sess_long(a,b)
    y=r.set_index('t').ret_bps.groupby(lambda x:x.year).mean().round(2)
    print(f"long {a}->{b}: n={len(r)} net_mean={r.ret_bps.mean():.2f}bps t={r.ret_bps.mean()/(r.ret_bps.std()/np.sqrt(len(r))):.2f} wr={(r.pnl>0).mean():.3f} yearly={list(y.values)}")
# buy & hold benchmark
bh=(np.log(mid.iloc[-1])-np.log(mid.iloc[0]))
print("buy&hold total log ret",round(bh,3), "CAGR", round((np.exp(bh/10)-1)*100,2),"%")
