import pandas as pd,numpy as np,lab
b=lab.make('1h'); BPY=24*252
lg=np.log(b.c)
hour=b.index.hour
# overnight window position 20:00->00:00 UTC (bar close 20 .. 23) => position on during hours 20,21,22,23
win=pd.Series(((hour>=20)&(hour<=23)).astype(float),index=b.index)
trend=(lg-lg.shift(240))  # 10-day
res={}
def ev(pos,name,vt=0.10,cap=10):
    r=lab.evaluate(b,pos,BPY,vol_target=vt,cap=cap,name=name)
    res[name]=r
    print(f"{name}: Sh={r['sharpe']:.2f} CAGR={r['cagr']:.2f}% vol={r['vol']:.2f}% DD={r['maxdd']:.1f}% calmar={r['calmar']:.2f} cost={r['cost_drag']:.2f}%/yr turn={r['turnover']:.0f}")
ev(win,'ON drift raw')
ev(win*(trend>0).astype(float),'ON drift trend>0')
ev(pd.Series(1.0,index=b.index),'BuyHold')
ev(win*np.tanh(trend/b.ret.rolling(500).std()/np.sqrt(240)).clip(0,None),'ON drift trend-scaled long')
# combine BH-lite + overnight
ev(0.3+0.7*win,'BH0.3 + ON')
