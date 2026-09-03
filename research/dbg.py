import pandas as pd,numpy as np,strategy as S
d=S.load(); m5=S.build_m5(d)
sg=S.signals(m5,z_th=2.5)
rng=np.random.default_rng(0)
sg2=sg.copy(); sg2['sig']=0
idx=rng.choice(len(sg2),3000,replace=False)
sg2.iloc[idx, sg2.columns.get_loc('sig')]=rng.choice([-1,1],3000)
for sl in (1,3,8):
  tr=S.backtest(d,sg2,tp_mult=sl,sl_mult=sl,max_bars_m1=1440,comm_usd=0.0,slip=0.0)
  m=S.metrics(tr,sl_mult=sl)
  print("RANDOM sl",sl,"n",m['trades'],"wr",round(m['win_rate'],3),"avgR",round(m['avg_R'],4),"tp%",round(m['pct_tp'],2),"time%",round(m['pct_time'],2),"avgbars",round(m['avg_bars_held'],1))
