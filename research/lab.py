"""Vectorised position-level backtest in RETURN space with realistic costs."""
import pandas as pd, numpy as np

d=pd.read_parquet('m1.parquet').set_index('timestamp').sort_index()
mid=(d.close_bid+d.close_ask)/2
sp=(d.close_ask-d.close_bid)

def make(rule):
    b=pd.DataFrame({'o':mid.resample(rule).first(),'h':mid.resample(rule).max(),
      'l':mid.resample(rule).min(),'c':mid.resample(rule).last(),
      'sp':sp.resample(rule).median()}).dropna()
    b['ret']=np.log(b.c).diff()
    b['cost_bps']=(b.sp/b.c*1e4)/2 + 0.5   # half-spread per side + 0.5bp slip/comm
    return b

def evaluate(b,pos,bars_per_year,vol_target=0.10,cap=3.0,name=''):
    p=pos.shift(1).fillna(0)
    # vol target scaling on realized vol of underlying
    rv=b.ret.rolling(24*20).std()*np.sqrt(bars_per_year)
    lev=(vol_target/rv).clip(0,cap).shift(1).fillna(0)
    e=p*lev
    gross=e*b.ret
    turn=e.diff().abs().fillna(0)
    cost=turn*b.cost_bps/1e4
    net=(gross-cost).fillna(0)
    ann=net.mean()*bars_per_year
    vol=net.std()*np.sqrt(bars_per_year)
    sh=ann/vol if vol>0 else 0
    eq=(1+net).cumprod()
    dd=(eq/eq.cummax()-1).min()
    yrs=(b.index[-1]-b.index[0]).days/365.25
    cagr=eq.iloc[-1]**(1/yrs)-1
    return dict(name=name,sharpe=sh,cagr=cagr*100,vol=vol*100,maxdd=dd*100,
                turnover=turn.sum()/yrs,cost_drag=cost.sum()/yrs*100,
                calmar=cagr/abs(dd) if dd<0 else np.inf, net=net, eq=eq, expo=e)
