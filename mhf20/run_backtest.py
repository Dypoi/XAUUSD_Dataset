import sys; sys.path.insert(0,'/home/user/XAUUSD_Dataset/mhf20')
from load_data import load_m5
from engine import run_backtest
from strategy import CFG
print("="*70); print("MHF-20 BACKTEST"); print("="*70)
df = load_m5()
print(f"Data: {len(df):,} bar M5, {df.index[0]} .. {df.index[-1]}\n")
res = run_backtest(df, CFG)
tr = res['trades']
tr.to_parquet('/home/user/XAUUSD_Dataset/mhf20/trades.parquet')
print(f"\nTersimpan: mhf20/trades.parquet ({len(tr):,} baris)")
