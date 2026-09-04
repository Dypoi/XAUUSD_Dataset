# MHF-20

**M**omentum continuation · **H**igh-**F**requency · Risk **$20**/posisi

Sistem long-only XAUUSD: sweep BSL sesi → displacement → filter bias H4, dieksekusi
lewat 8 slot paralel dengan time-stop 24 jam.

## Hasil backtest (2016-09 → 2026-09, net biaya)

| Metrik | Nilai |
|---|---|
| Trades | 6.274 (2,54/hari) |
| Win rate | 53,70% |
| Profit Factor | 1,213 |
| Equity | $10.000 → $22.567 (+125,7%) |
| CAGR | 8,65% |
| Max Drawdown | −14,47% |
| Ekspektasi | +$2,00 (+0,100R) |
| t-stat | +6,89 |

Validasi: kontrol entry acak PF 1,033 · IS 1,145 / OOS 1,232 · bertahan sampai +5 pips biaya.

## Pakai

```bash
/home/user/.venv/bin/python run_backtest.py
```

```python
from load_data import load_m5
from engine import run_backtest
from strategy import CFG
res = run_backtest(load_m5(), CFG)
```

## Berkas
- `strategy.py` — konfigurasi + sinyal (BSL/SSL kausal, bias H4, sizing)
- `engine.py` — backtester multi-posisi bid/ask
- `load_data.py` — loader M1 → M5
- `docs/HONEST_LIMITS.md` — **baca ini** sebelum live

## Aturan yang TIDAK boleh diubah
1. **Long-only.** Short diuji: PF 0,748.
2. **Risiko total ≤ $160.** 8 slot × $80 → DD −57%.
3. **BSL/SSL pakai cummax dalam hari.** `groupby.transform('max')` = look-ahead, +0,30 PF palsu.
4. **Urutan: struktur → SL → lot.** Jangan pernah tentukan lot dulu.
