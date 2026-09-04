
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

---

## MODE SANTAI — maks 1 entry/hari (permintaan pengguna)

Default berubah. Sistem kini masuk **maksimal 1 trade/hari** dengan risiko $100 (naik
dari $20) dan 2 slot (turun dari 8).

| | Standar v1.1 | **Santai (aktif)** |
|---|---|---|
| Entry/hari | 2,03 | **maks 1** (rata2 0,31) |
| Trades | 4.905 | 740 |
| Risiko/trade | $20 | **$100** |
| Risiko maks terbuka | $800 | **$200** |
| PF | 1,304 | **1,362** |
| CAGR | 9,50% | 7,20% |
| MaxDD | −11,68% | **−10,43%** |
| t-stat | +8,43 | +3,77 |

IS 1,215 / OOS **1,482** · tahan +$0,50/sisi (PF 1,176).

**PENTING: 75% hari tidak ada sinyal.** Rata-rata nyata 0,31/hari ≈ 1 trade per 3 hari
kerja. Membatasi 1/hari memangkas hari sibuk tapi tidak menciptakan sinyal di hari sepi.

Ditegakkan di live (`executor.py` menolak order ke-2: "Mode santai: batas 1 entry/hari
sudah terpakai"). Tes **[24]** memaksa `MAX_ENTRIES_PER_DAY`/`MAX_CONCURRENT`/
`RISK_PER_POSITION` identik antara backtest dan live.

Audit: **paritas 191/191 · resilience 78/78 · eksekusi 38/38**.
Verifikasi: `test_resilience.py` → **`LULUS 78 · GAGAL 0`**, `test_execution.py` → **38**.

Balik ke standar: set `MAX_ENTRIES_PER_DAY=0`, `RISK_PER_POSITION=20`, `MAX_CONCURRENT=8`,
`BIAS_MIN_DIST_PCT=0.50`, `MAX_ORDERS_PER_DAY=12` di **kedua** file.

Detail: `docs/MODE_SANTAI.md`

---

## MODE AKTIF — maks 5 entry/hari (permintaan pengguna, menggantikan mode santai)

| | Standar | Santai (1/hr) | **Aktif (5/hr)** |
|---|---|---|---|
| Entry/hari nyata | 2,03 | 0,31 | **1,15** |
| Trades | 4.905 | 740 | **2.779** |
| Risiko/trade | $20 | $100 | **$40** |
| Slot | 8 | 2 | **8** |
| WR | 55,33% | 55,27% | **55,70%** |
| PF | 1,304 | 1,362 | **1,353** |
| CAGR | 9,50% | 7,20% | **9,10%** |
| MaxDD | −11,68% | −10,43% | **−11,83%** |
| t-stat | +8,43 | +3,77 | **+7,16** |

IS 1,382 / OOS 1,330 · tahan +$0,50/sisi (PF 1,171). **Jan–Ags 2026 PF 0,961 (−$131).**

Mode aktif ≈ CAGR mode standar dengan 43% lebih sedikit trade dan PF lebih tinggi.

**BUG DIPERBAIKI:** cap harian dihitung pada hari *sinyal* (`day[i]`) padahal entry
dieksekusi bar berikutnya (`day[j]`) → ada hari dengan 6 entry meski cap 5. Sekarang
dikunci ke hari eksekusi. Verifikasi: maks 5/hari, nol pelanggaran.

**75% hari tetap tanpa sinyal.** 411 hari langsung mentok cap 5; sisanya sepi.

Pembulatan lot: risk $30 = risk $20 (sama-sama 0,02 lot). $40 → 0,03 lot = $36,84 nyata.

Audit: **paritas 191/191 · resilience 78/78 · eksekusi 38/38**.

Detail + cara ganti mode: `docs/MODE_AKTIF.md`
