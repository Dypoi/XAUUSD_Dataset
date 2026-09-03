import pandas as pd,numpy as np
d=pd.read_parquet('m1.parquet').set_index('timestamp').sort_index()
mid=(d.close_bid+d.close_ask)/2
def bars(rule):
    b=pd.DataFrame({'o':mid.resample(rule).first(),'h':mid.resample(rule).max(),
      'l':mid.resample(rule).min(),'c':mid.resample(rule).last(),
      'sp':(d.close_ask-d.close_bid).resample(rule).median()}).dropna()
    return b
def atr_f(b,n):
    tr=pd.concat([b.h-b.l,(b.h-b.c.shift()).abs(),(b.l-b.c.shift()).abs()],axis=1).max(axis=1)
    return tr.rolling(n).mean()
def bt(b,pos,cost_usd):
    # pos: target position (-1/0/1) known at bar close, applied to next bar return
    p=pos.shift(1).fillna(0)
    ret=b.c.diff()                     # usd per oz
    pnl=p*ret
    trades=p.diff().abs().fillna(0)
    pnl-= trades*cost_usd
    return pnl,p,trades
res=[]
for rule in ('1h','4h'):
    b=bars(rule); a=atr_f(b,20)
    cost=b.sp.median()+0.04+0.07  # spread + slippage + commission per side... approx
    for n in (24,48,96,168,336):
        hh=b.h.rolling(n).max().shift(1); ll=b.l.rolling(n).min().shift(1)
        for exitn in (n//2,n//4):
            xh=b.h.rolling(exitn).max().shift(1); xl=b.l.rolling(exitn).min().shift(1)
            pos=pd.Series(np.nan,index=b.index)
            pos[b.c>hh]=1; pos[b.c<ll]=-1
            pos[(b.c<xl)]=np.where(pos[(b.c<xl)].fillna(0)>0,0,pos[(b.c<xl)])
            pos=pos.ffill().fillna(0)
            # simple: long while c>ll_exit, handled crudely
            pnl,p,tr=bt(b,pos,cost)
            eq=pnl.cumsum()
            dd=(eq-eq.cummax()).min()
            sh=pnl.mean()/pnl.std()*np.sqrt(252*(24 if rule=='1h' else 6))
            # normalize by price to get % terms
            pct=(pnl/b.c.shift(1)).fillna(0)
            eqp=(1+pct*1).cumprod()
            res.append((rule,n,exitn,round(pnl.sum(),1),round(sh,2),int(tr.sum()),round(dd,1)))
for r in sorted(res,key=lambda x:-x[4])[:20]: print(r)
