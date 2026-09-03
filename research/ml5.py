import pandas as pd,numpy as np,lab
b=lab.make('5min'); BPY=288*252
c=np.log(b.c)
r=b.ret
vol=r.rolling(288).std()
X=pd.DataFrame(index=b.index)
for n in (3,6,12,24,48,96,288):
    X[f'mom{n}']=(c-c.shift(n))/(vol*np.sqrt(n))
X['rng']=((b.c-b.l.rolling(48).min())/(b.h.rolling(48).max()-b.l.rolling(48).min())-0.5).fillna(0)
X['volr']=np.log(vol/vol.rolling(2016).mean())
X['hr_sin']=np.sin(2*np.pi*b.index.hour/24); X['hr_cos']=np.cos(2*np.pi*b.index.hour/24)
X['dow']=b.index.dayofweek
H=12
y=(c.shift(-H)-c)/ (vol*np.sqrt(H))
data=pd.concat([X,y.rename('y')],axis=1).replace([np.inf,-np.inf],np.nan).dropna()
Xa=data.drop(columns='y').values; ya=np.clip(data.y.values,-5,5)
idx=data.index
# walk-forward ridge, yearly refit
pred=pd.Series(np.nan,index=idx)
years=sorted(set(idx.year))
from numpy.linalg import solve
for yr in years[2:]:
    tr=idx.year<yr; te=idx.year==yr
    if tr.sum()<10000 or te.sum()==0: continue
    Xt=Xa[tr]; mu=Xt.mean(0); sd=Xt.std(0)+1e-9
    Xt=(Xt-mu)/sd; yt=ya[tr]
    A=Xt.T@Xt+ len(Xt)*1e-2*np.eye(Xt.shape[1]); w=solve(A,Xt.T@yt)
    pred[te]=((Xa[te]-mu)/sd)@w
p=pred.dropna()
print("pred IC:",np.corrcoef(p, pd.Series(ya,index=idx).loc[p.index])[0,1].round(4))
sig=np.tanh(p/p.std()*1.0).reindex(b.index).fillna(0)
# hold H bars: average of overlapping signals
pos=sig.rolling(H).mean().fillna(0)
for cap in (1,2,3):
    res=lab.evaluate(b,pos,BPY,cap=cap,name=f'ml5 cap{cap}')
    print({k:round(v,3) for k,v in res.items() if k in('sharpe','cagr','vol','maxdd','turnover','cost_drag')})
# gross (no cost) sanity
res=lab.evaluate(b.assign(cost_bps=0),pos,BPY,name='ml5 nocost')
print("gross:",{k:round(v,3) for k,v in res.items() if k in('sharpe','cagr','cost_drag')})
