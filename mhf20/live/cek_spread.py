"""Diagnostik spread — pastikan angka dashboard cocok dengan broker Anda.

Jalankan dengan MT5 terbuka:
    .venv\Scripts\python cek_spread.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import CFG

try:
    import MetaTrader5 as mt5
except ImportError:
    print("Paket MetaTrader5 tidak ada (butuh Windows + Python 3.11/3.12).")
    sys.exit(1)

if not mt5.initialize():
    print("MT5 tidak bisa dibuka:", mt5.last_error())
    print("Pastikan MT5 terbuka, login, dan AutoTrading aktif.")
    sys.exit(1)

sym = CFG.SYMBOL
if mt5.symbol_info(sym) is None:
    cand = [s.name for s in mt5.symbols_get() if "XAU" in s.name.upper()]
    print(f"Simbol {sym} tidak ada. Yang tersedia: {cand}")
    sym = cand[0] if cand else None
    if not sym: sys.exit(1)
mt5.symbol_select(sym, True)

si = mt5.symbol_info(sym)
tk = mt5.symbol_info_tick(sym)
r = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M5, 0, 1)

print(f"\n{'='*58}\n  DIAGNOSTIK SPREAD — {sym}\n{'='*58}")
print(f"  digits            : {si.digits}")
print(f"  point             : {si.point}")
print(f"  bid / ask         : {tk.bid:.3f} / {tk.ask:.3f}")

real = tk.ask - tk.bid
print(f"\n  Spread NYATA (ask-bid)      : ${real:.3f}   <-- acuan kebenaran")

if r is not None and len(r):
    raw = float(r[0]['spread'])
    print(f"  spread mentah bar (point)   : {raw:.0f}")
    print(f"  konversi BENAR  raw*point   : ${raw*si.point:.3f}")
    print(f"  konversi LAMA   raw/100     : ${raw/100:.3f}", end="")
    print("   <-- SALAH kalau digits=3" if si.digits == 3 else "")

print(f"\n  Ambang guard MAX_SPREAD_USD : ${CFG.MAX_SPREAD_USD}")
if real <= CFG.MAX_SPREAD_USD:
    print(f"  STATUS: LOLOS — entry diizinkan (${real:.3f} <= ${CFG.MAX_SPREAD_USD})")
else:
    print(f"  STATUS: DIBLOKIR — spread sedang lebar (${real:.3f} > ${CFG.MAX_SPREAD_USD})")
    print("          Normal saat rollover 00:00 server atau rilis berita.")

print(f"\n  Asumsi backtest: median $0.337 (~3.4 pips)")
print(f"  Iklan Exness   : ~$0.26")
if real > 1.2:
    print("\n  CATATAN: kalau angka ini tetap >$1.2 padahal pasar tenang,")
    print("           kemungkinan akun Anda spread-nya memang lebar.")
print("="*58)
mt5.shutdown()
