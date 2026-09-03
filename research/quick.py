import pandas as pd,numpy as np,strategy as S
d=S.load(); m5=S.build_m5(d)
for z in (2.0,2.5,3.0):
 for tp,sl in ((1.0,1.0),(1.0,1.5),(1.5,1.5),(0.75,1.0),(1.5,2.0)):
  sg=S.signals(m5,z_th=z)
  tr=S.backtest(d,sg,tp_mult=tp,sl_mult=sl,max_bars_m1=240,comm_usd=0.10,slip=0.02)
  m=S.metrics(tr,sl_mult=sl)
  print(f"z{z} tp{tp} sl{sl}: n={m['trades']:5d} wr={m['win_rate']:.3f} PF={m['profit_factor']:.3f} avgR={m['avg_R']:+.4f} t={m['t_stat']:+.2f} CAGR={m['cagr_pct']:.1f}% DD={m['max_dd_pct']:.1f}% Sh={m['sharpe_daily']:.2f}")
