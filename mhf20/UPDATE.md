
---

## v1.1 — Filter Kualitas Tren H4 (jawaban atas pertanyaan "bagaimana dengan tren market?")

Bias H4 lama cuma biner (`close > MA240`). Ditemukan dua kantong rugi:
- MA240 sudah **berbalik turun** tapi harga masih di atasnya → PF 0,910 (−$1.108)
- Harga **mendempet** MA240 (zona whipsaw) → PF 0,763 (−$2.952) ← kantong rugi terbesar

Dua syarat baru (kausal, bisa dimatikan dengan nilai 0):
```python
BIAS_SLOPE_BARS   = 30     # MA240 harus menanjak (~5 hari H4)
BIAS_MIN_DIST_PCT = 0.50   # harga min 0,50% di atas MA240
```

| | v1.0 | v1.1 |
|---|---|---|
| Trades | 6.274 | 4.905 (−22%) |
| WR | 53,70% | **55,33%** |
| PF | 1,213 | **1,304** |
| CAGR | 8,65% | **9,50%** |
| MaxDD | −14,47% | **−11,68%** |
| t-stat | +6,89 | **+8,43** |
| IS / OOS | 1,132 / 1,281 | **1,276 / 1,324** |
| PF @ +$0,20 slippage | 1,004 | **1,230** |
| PF @ +$0,50 slippage | 0,728 | **1,006** |

Sensitivitas: **25/25 kombinasi parameter mengungguli baseline** — dataran, bukan tebing.

`live/signal_engine.py` + `live/config.py` disinkronkan (punya salinan `macro_bias` sendiri).
Tes **[23]** memaksa nilai `BIAS_*` identik antara backtest dan live, dan membuktikan filter
benar-benar menolak/meloloskan. Panel dashboard kini menampilkan MA240, jarak %, dan slope.

Audit: **paritas 191/191 · resilience 69/69 · eksekusi 37/37**.
Verifikasi: `tests\test_resilience.py` harus berakhir **`LULUS 69 · GAGAL 0`**.

Detail lengkap: `docs/FILTER_TREN.md`
