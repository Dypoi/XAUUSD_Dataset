import pandas as pd,numpy as np,json
import final_strategy as F
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt

b=F.load_bars('4h'); ens,raw=F.signal(b)
r=F.backtest(b,raw)
bh=F.backtest(b,pd.Series(1.0,index=b.index))
res={}
res['full']=F.stats(r,label='Strategy FULL 2016-09..2026-09')
res['bh_full']=F.stats(bh,label='Buy&Hold vol-targeted FULL')
res['IS']=F.stats(r.loc[:'2021-08'],label='Strategy IS 2016-09..2021-08')
res['OOS']=F.stats(r.loc['2021-09':],label='Strategy OOS 2021-09..2026-09')
res['bh_OOS']=F.stats(bh.loc['2021-09':],label='Buy&Hold OOS')
# yearly
yr=[]
for y,g in r.groupby(r.index.year):
    gb=bh.loc[g.index]
    eq=(1+g.net).cumprod(); dd=(eq/eq.cummax()-1).min()
    yr.append(dict(year=y,ret_pct=round((eq.iloc[-1]-1)*100,2),
        maxdd_pct=round(dd*100,2),
        bh_pct=round(((1+gb.net).cumprod().iloc[-1]-1)*100,2),
        avg_expo=round(g.expo.mean(),2),
        sharpe=round(g.net.mean()*6*252/(g.net.std()*np.sqrt(6*252)),2)))
yearly=pd.DataFrame(yr)
# monthly table
m=(1+r.net).resample('ME').prod()-1
mt=pd.DataFrame({'y':m.index.year,'m':m.index.month,'r':m.values}).pivot(index='y',columns='m',values='r')*100
# regime / robustness
rob=[]
for th in (-0.6,-0.5,-0.35,-0.2,0.0):
  for fl in (0.0,0.25,0.4):
    p=fl+(1-fl)*(ens>th).astype(float)
    s=F.stats(F.backtest(b,p))
    rob.append(dict(thresh=th,floor=fl,sharpe=s['sharpe'],cagr=s['cagr_pct'],dd=s['max_dd_pct'],calmar=s['calmar']))
rob=pd.DataFrame(rob)
# param sensitivity on horizons
sens=[]
c=np.log(b.c); v=b.ret.rolling(500).std()
for n1,n2,n3 in [(60,180,540),(90,240,720),(120,240,720),(120,360,1080),(180,540,1080),(240,720,1440)]:
    e=(np.tanh((c-c.shift(n1))/(v*np.sqrt(n1)))+np.tanh((c-c.shift(n2))/(v*np.sqrt(n2)))+np.tanh((c-c.shift(n3))/(v*np.sqrt(n3))))/3
    p=0.25+0.75*(e>-0.35).astype(float)
    s=F.stats(F.backtest(b,p)); sens.append(dict(horizons=f"{n1}/{n2}/{n3}",sharpe=s['sharpe'],cagr=s['cagr_pct'],dd=s['max_dd_pct'],calmar=s['calmar']))
sens=pd.DataFrame(sens)
# cost stress
cost=[]
for mult,extra in [(1,0),(1,1),(1,2),(2,0),(3,0),(1,5)]:
    b2=b.copy(); b2['cost_bps']=b.cost_bps*mult+extra
    s=F.stats(F.backtest(b2,raw)); cost.append(dict(spread_mult=mult,extra_bps=extra,sharpe=s['sharpe'],cagr=s['cagr_pct'],dd=s['max_dd_pct']))
cost=pd.DataFrame(cost)
# monte carlo block bootstrap on daily returns
daily=(1+r.net).resample('D').prod().dropna()-1
rng=np.random.default_rng(42); bl=20; arr=daily.values; nb=len(arr)//bl
sims=[]
for _ in range(2000):
    idx=rng.integers(0,len(arr)-bl,nb)
    path=np.concatenate([arr[i:i+bl] for i in idx])
    eq=(1+path).cumprod(); sims.append([eq[-1]**(252/len(path))-1,(eq/np.maximum.accumulate(eq)-1).min()])
sims=np.array(sims)
mc=dict(cagr_p5=round(np.percentile(sims[:,0],5)*100,2),cagr_p50=round(np.percentile(sims[:,0],50)*100,2),
        cagr_p95=round(np.percentile(sims[:,0],95)*100,2),dd_p95=round(np.percentile(sims[:,1],5)*100,2),
        prob_positive=round((sims[:,0]>0).mean()*100,1))
# deflated-ish: t-stat
t=r.net.mean()/(r.net.std()/np.sqrt(len(r)))
# charts
fig,ax=plt.subplots(3,1,figsize=(12,12),sharex=True)
ax[0].plot(r.index,(1+r.net).cumprod(),label='XAU-TRV strategy',lw=1.4)
ax[0].plot(bh.index,(1+bh.net).cumprod(),label='Buy&Hold (same vol target)',lw=1,alpha=.7)
ax[0].set_yscale('log'); ax[0].legend(); ax[0].set_title('Equity curve (log), net of costs'); ax[0].grid(alpha=.3)
eq=(1+r.net).cumprod(); ax[1].fill_between(r.index,(eq/eq.cummax()-1)*100,0,color='crimson',alpha=.6)
ax[1].set_title('Drawdown %'); ax[1].grid(alpha=.3)
ax[2].plot(r.index,r.expo,lw=.7); ax[2].set_title('Exposure (leverage on 1 unit gold)'); ax[2].grid(alpha=.3)
plt.tight_layout(); plt.savefig('/home/user/XAUUSD_Dataset/reports/equity.png',dpi=110)
fig2,ax2=plt.subplots(figsize=(10,4))
yearly.set_index('year')[['ret_pct','bh_pct']].plot(kind='bar',ax=ax2); ax2.set_title('Yearly net return: strategy vs buy&hold'); ax2.grid(alpha=.3)
plt.tight_layout(); plt.savefig('/home/user/XAUUSD_Dataset/reports/yearly.png',dpi=110)
out=dict(headline=res,mc=mc,t_stat=round(float(t),2))
json.dump(out,open('/home/user/XAUUSD_Dataset/reports/metrics.json','w'),indent=2,default=str)
yearly.to_csv('/home/user/XAUUSD_Dataset/reports/yearly.csv',index=False)
mt.round(2).to_csv('/home/user/XAUUSD_Dataset/reports/monthly.csv')
rob.to_csv('/home/user/XAUUSD_Dataset/reports/robustness_params.csv',index=False)
sens.to_csv('/home/user/XAUUSD_Dataset/reports/robustness_horizons.csv',index=False)
cost.to_csv('/home/user/XAUUSD_Dataset/reports/cost_stress.csv',index=False)
r.to_parquet('/home/user/XAUUSD_Dataset/reports/strategy_series.parquet')
print(json.dumps(out,indent=2,default=str))
print(yearly.to_string(index=False)); print(mt.round(2).to_string())
print(rob.to_string(index=False)); print(sens.to_string(index=False)); print(cost.to_string(index=False))
