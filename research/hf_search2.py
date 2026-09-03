import pandas as pd, numpy as np
from hf_engine import sim_par
d=pd.read_parquet('m1.parquet').set_index('timestamp').sort_index()
m5=pd.DataFrame({
 'o':((d.open_bid+d.open_ask)/2).resample('5min').first(),
 'h':((d.high_bid+d.high_ask)/2).resample('5min').max(),
 'l':((d.low_bid+d.low_ask)/2).resample('5min').min(),
 'c':((d.close_bid+d.close_ask)/2).resample('5min').last(),
 'ob':d.open_bid.resample('5min').first(),'oa':d.open_ask.resample('5min').first(),
 'hb':d.high_bid.resample('5min').max(),'la':d.low_ask.resample('5min').min(),
 'lb':d.low_bid.resample('5min').min(),'ha':d.high_ask.resample('5min').max(),
}).dropna()
day=m5.index.normalize()
dayid=np.asarray(day.view('int64')//86_400_000_000,dtype=np.int64)
A=[m5.ob.values,m5.oa.values,m5.hb.values,m5.lb.values,m5.ha.values,m5.la.values,dayid]
NB=10*252

def run(sig,sl=12.0,rr=2.0,risk=80.0,eq0=10000.0,conc=3,maxday=99,ts=288,slip=0.02,dl=1e9,dp=1e9):
    e,x,p,s,eq=sim_par(sig,*A,sl,rr,risk,eq0,conc,maxday,ts,slip,dl,dp)
    if len(p)<30: return None
    tr=pd.DataFrame({'t':m5.index[e],'exit':m5.index[x],'usd':p,'side':s,'eq':eq}).set_index('t').sort_index()
    ec=pd.Series(tr['eq'].to_numpy(),index=tr.index)
    gp=p[p>0].sum(); gl=-p[p<0].sum()
    yrs=(tr.index[-1]-tr.index[0]).days/365.25
    return dict(tr=tr,n=len(p),wr=(p>0).mean()*100,pf=gp/max(gl,1e-9),net=p.sum(),
      final=eq[-1],dd=(ec/ec.cummax()-1).min()*100,perday=len(p)/NB,
      t=p.mean()/(p.std()/np.sqrt(len(p))),yrs=yrs,ec=ec,
      cagr=((eq[-1]/eq0)**(1/yrs)-1)*100 if eq[-1]>0 else -100)

lg=np.log(m5.c); atr=(m5.h-m5.l).rolling(48).mean()
h4=m5.c.resample('4h').last().dropna()
bias=(h4>h4.rolling(240).mean()).reindex(m5.index,method='ffill').fillna(False)
bias100=(h4>h4.rolling(100).mean()).reindex(m5.index,method='ffill').fillna(False)
sw_h=m5.h.shift(2).rolling(5).max()
bfvg=m5.l>(m5.h.shift(2)+0.30)
bull_disp=(m5.c>m5.o)&((m5.c>sw_h)|bfvg)
hh=m5.index.hour; day_=m5.index.normalize()
asia=(hh<7); lon=(hh>=7)&(hh<12)
ah=m5.h.where(asia).groupby(day_).cummax().ffill(); lh=m5.h.where(lon).groupby(day_).cummax().ffill()
BSL=pd.concat([ah,lh],axis=1).max(axis=1)
bsl_swept=(m5.h.shift(1)>=BSL)|(m5.h.shift(2)>=BSL)
Z=pd.Series(False,index=m5.index)
def mk(b): return np.where(b.fillna(False),1,0).astype(np.int64)

print("="*128)
print("SETUP FREKUENSI TINGGI — engine multi-posisi (maks 3 paralel) + time stop")
print("="*128)
print(f"{'Setup':40s} {'conc':>4s} {'TS':>4s} {'n':>6s} {'/hari':>6s} {'WR%':>6s} {'PF':>7s} {'Final$':>10s} {'DD%':>7s} {'t':>6s}")
print("-"*128)
base={'v2_bias240':bsl_swept&bull_disp&bias,
      'v2_bias100':bsl_swept&bull_disp&bias100,
      'v2_nobias':bsl_swept&bull_disp}
rows=[]
for nm,sg in base.items():
    s=mk(sg)
    for conc in (1,3,5):
        for ts in (72,144,288):
            r=run(s,conc=conc,ts=ts)
            if not r: continue
            rows.append((f"{nm} c{conc} ts{ts}",r))
            print(f"{nm:40s} {conc:4d} {ts:4d} {r['n']:6d} {r['perday']:6.2f} {r['wr']:6.2f} {r['pf']:7.3f} {r['final']:10,.0f} {r['dd']:7.1f} {r['t']:+6.2f}")
print()
ok=[(n,r) for n,r in rows if r['perday']>=2.0 and r['pf']>1.0]
print(f">=2/hari & PF>1 : {len(ok)}")
for n,r in sorted(ok,key=lambda x:-x[1]['pf'])[:10]:
    print(f"   {n:34s} PF={r['pf']:.3f} /hari={r['perday']:.2f} final=${r['final']:,.0f} DD={r['dd']:.1f}%")
