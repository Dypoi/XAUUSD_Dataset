"""AUDIT FORENSIK 1 — Paritas live vs backtest.

Memutar ulang data historis lewat mesin LIVE secara bar-per-bar (hanya bar tertutup,
hanya data masa lalu) lalu membandingkan sinyalnya dengan mesin BACKTEST.
Selisih satu pun = bug fatal.
"""
import sys, os
_L = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # .../mhf20/live
_M = os.path.dirname(_L)                                           # .../mhf20
sys.path[:0] = [_L, _M]
import numpy as np, pandas as pd
from strategy import compute_signals, CFG as BCFG
import signal_engine as LE

df = pd.read_parquet('/home/user/XAUUSD_Dataset/mhf20/live/cache/m5.parquet')
seg = df.iloc[620000:648000].copy()  # 28k bar: cukup untuk MA240 H4
bt = compute_signals(seg, BCFG)['long_signal'].to_numpy()

live_sig = np.zeros(len(seg), bool)
start = 24000
for i in range(start, len(seg)):
    win = seg.iloc[max(0, i-20000):i+1]      # HANYA sampai bar i (tanpa masa depan)
    ev = LE.evaluate_closed_bar(win, 0, 0.0, 10000.0, 10000.0)
    live_sig[i] = ev.ctx.get('sig_ok', False) if ev.ctx else False

a, b = bt[start:], live_sig[start:]
mism = np.where(a != b)[0]
print(f"Bar dibandingkan : {len(a):,}")
print(f"Sinyal backtest  : {a.sum():,}")
print(f"Sinyal live      : {b.sum():,}")
print(f"Ketidakcocokan   : {len(mism)}")
if len(mism):
    print("CONTOH MISMATCH:", [(str(seg.index[start+j]), bool(a[j]), bool(b[j])) for j in mism[:5]])
    print("HASIL: GAGAL"); sys.exit(1)
print("HASIL: LULUS — mesin live identik dengan backtest")
