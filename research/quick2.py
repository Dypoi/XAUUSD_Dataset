import pandas as pd,numpy as np,strategy as S
d=S.load(); m5=S.build_m5(d)
sg=S.signals(m5,z_th=2.5)
print("ATR usd stats:",sg.atr.describe([.1,.5,.9]).round(3).to_dict())
print("spread usd median:",(d.close_ask-d.close_bid).median())
for sl in (3,5,8,12):
 for tpr in (0.5,1.0,1.5,2.0):
  tr=S.backtest(d,sg,tp_mult=sl*tpr,sl_mult=sl,max_bars_m1=360,comm_usd=0.10,slip=0.02)
  m=S.metrics(tr,sl_mult=sl,risk_per_trade=0.005)
  print(f"sl{sl}ATR tp{sl*tpr}: n={m['trades']:5d} wr={m['win_rate']:.3f} PF={m['profit_factor']:.3f} avgR={m['avg_R']:+.4f} t={m['t_stat']:+.2f} CAGR={m['cagr_pct']:.1f}% DD={m['max_dd_pct']:.1f}% Sh={m['sharpe_daily']:.2f} tp%={m['pct_tp']:.2f} time%={m['pct_time']:.2f}")
