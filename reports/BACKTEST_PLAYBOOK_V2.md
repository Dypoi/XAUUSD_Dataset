# Backtest Playbook v2 — Hasil Setelah 3 Perbaikan Diterapkan

**Modal awal:** $10,000 · **Risk:** $80/trade · **Maks:** 2 trade/hari · **SL:** $12 (120 pips, CISD M5) · **RR:** 1:2
**Periode:** 2016-09 → 2026-09 (9.8 tahun) · **Biaya:** spread bid/ask aktual dataset + slippage $0.02/oz
**Kode:** `research/playbook_v2.py`, `playbook_v2_report.py`, `playbook_v2_robust.py`

---

## JAWABAN LANGSUNG

| Pertanyaan Anda | **Jawaban** |
|---|---|
| **Profit Factor?** | **1.275** |
| **Win rate?** | **54.93%** |
| **Max Drawdown?** | **−5.61%** |
| **$10,000 jadi berapa?** | **$18,766** (+87.7%, CAGR 6.63%) |
| **Entry per hari?** | **0.37/hari** (1.81 per minggu) |

Ini konfigurasi terbaik: **V2 LONG-ONLY**. Detail dan alternatifnya di bawah.

---

## 1. Dampak Ketiga Perbaikan

| Konfigurasi | n | WR% | **PF** | **Final $10k** | **DD%** | entry/hari |
|---|---|---|---|---|---|---|
| **V1 playbook ASLI** (tanpa perbaikan) | 1,781 | 46.77 | **0.863** | **$−1 (BANGKRUT)** | −100.0 | 0.71 |
| V1 asli + gerbang killzone | 995 | 46.63 | 0.845 | $3,626 | −69.0 | 0.39 |
| V2 fix-1 saja (Judas dibalik) | 2,176 | 49.59 | 1.014 | $11,201 | −20.4 | 0.86 |
| V2 fix-1+2 (dibalik + bias D/H4) | 1,460 | 52.67 | 1.163 | $18,653 | −18.2 | 0.58 |
| **V2 LONG-ONLY** (SELL dimatikan total) | **923** | **54.93** | **1.275** | **$18,766** | **−5.61** | **0.37** |
| V2 long-only + gerbang killzone | 778 | 52.44 | 1.149 | $14,266 | −15.8 | 0.31 |

**Perubahan dari V1 ke V2 long-only: PF 0.863 → 1.275, dari bangkrut menjadi +87.7%, DD dari −100% menjadi −5.61%.**

**Kontribusi tiap perbaikan:**

| Perbaikan | Dampak PF | Catatan |
|---|---|---|
| **Fix-1: Balik Judas Swing** | 0.863 → 1.014 | **+0.151** — mengubah rugi jadi impas |
| **Fix-2: Bias D/H4 objektif** | 1.014 → 1.163 | **+0.149** — filter arah |
| **Fix-2b: SELL dimatikan total** | 1.163 → 1.275 | **+0.112** — dan DD turun 18.2% → 5.6% |
| **Fix-3: Hapus killzone** | 1.149 → 1.275 | **+0.126** — killzone justru merugikan |

Fix-3 terkonfirmasi: memasang gerbang killzone **menurunkan** PF dari 1.275 ke 1.149 dan menaikkan DD dari 5.6% ke 15.8%. Prinsip Anda *"jam adalah informasi, bukan izin"* terbukti benar secara kuantitatif.

---

## 2. Detail Konfigurasi Terbaik — V2 LONG-ONLY

```
Trades                 : 923  (9.8 tahun)
Win rate               : 54.93%
Profit Factor          : 1.275
Net P/L                : +$8,766
Balance $10,000     -> : $18,766   (+87.7%)
CAGR                   : 6.63%/tahun
Max Drawdown           : -5.61%
Avg win / avg loss     : +$80.20 / -$76.68   (payoff 1.05)
Expectancy per trade   : +$9.50
t-stat                 : +3.48
```

**Frekuensi entry:**

| Ukuran | Nilai |
|---|---|
| Per hari (rata-rata semua hari bursa) | **0.37** |
| Per hari (pada hari yang ada trade) | 1.27 |
| **Per minggu** | **1.81** |
| Hari aktif | 728 dari ~2,520 hari bursa (29%) |

Target playbook Anda 2–3 setup/minggu; hasil aktual **1.81/minggu** — sedikit lebih konservatif, masih di kisaran yang benar.

**Per tahun:**

| Tahun | n | PF | WR% | P/L | Equity akhir |
|---|---|---|---|---|---|
| 2016 | 3 | 1.01 | 66.67 | +$1 | $10,001 |
| 2017 | 50 | 1.20 | 56.00 | +$344 | $10,345 |
| 2018 | 31 | 1.01 | 51.61 | +$10 | $10,356 |
| 2019 | 62 | 1.43 | 56.45 | +$907 | $11,263 |
| 2020 | 105 | 1.60 | 60.00 | +$1,889 | $13,152 |
| 2021 | 55 | 0.97 | 54.55 | −$60 | $13,092 |
| 2022 | 74 | 1.15 | 50.00 | +$442 | $13,534 |
| 2023 | 89 | 1.15 | 51.69 | +$490 | $14,024 |
| 2024 | 138 | 1.42 | 56.52 | +$1,961 | $15,985 |
| 2025 | 225 | 1.35 | 56.44 | +$2,619 | $18,604 |
| 2026 | 91 | 1.05 | 49.45 | +$163 | $18,766 |

**10 dari 11 tahun profit.** Tahun terburuk hanya −$60 (2021). Tidak ada tahun bencana.

---

## 3. Validasi — Ini Bagian Terpenting

### A. Uji kontrol vs entry acak

Geometri SL/TP dan seluruh aturan risiko **identik**, hanya waktu entry diacak (long-only):

| | PF | Final $10k |
|---|---|---|
| Acak #1 | 0.976 | $7,865 |
| Acak #2 | 0.996 | $9,626 |
| Acak #3 | 1.046 | $13,853 |
| **Acak rata-rata 8 seed** | **1.005** | **$10,360** |
| **V2 LONG-ONLY** | **1.275** | **$18,766** |
| **Selisih** | **+0.270** | **+$8,407** |

**Ini pertama kalinya sebuah varian ICT/SMC lolos uji kontrol saya.** Bandingkan dengan bot ICAS: PF 0.880 vs acak 0.996 (selisih **−0.116**). Sinyalnya sekarang benar-benar menambah nilai, bukan sekadar menangkap drift.

### B. Split In-Sample / Out-of-Sample

| Periode | n | WR% | PF | Net | DD% | t-stat |
|---|---|---|---|---|---|---|
| **IS** 2016-09→2021-08 | 283 | 57.60 | **1.363** | +$3,360 | −5.61 | +2.44 |
| **OOS** 2021-09→2026-09 | 640 | 53.75 | **1.239** | +$5,406 | −6.70 | +2.56 |

Konsisten di kedua periode, keduanya signifikan (t > 2). OOS sedikit lebih rendah — normal dan sehat.

### C. Sensitivitas SL & RR

| SL | RR 1:1.5 | RR 1:2 | RR 1:3 |
|---|---|---|---|
| $8 (80p) | 1.118 | 1.143 | 1.167 |
| $10 (100p) | 1.221 | 1.254 | 1.309 |
| **$12 (120p)** | 1.230 | **1.275** | 1.276 |
| $15 (150p) | 1.246 | **1.363** | 1.347 |
| $20 (200p) | 1.302 | **1.367** | **1.403** |

**Semua 15 kombinasi PF > 1.11.** Tidak ada cliff — bukan hasil overfit. Menariknya SL lebih lebar ($15–20) justru lebih baik, konsisten dengan pernyataan playbook Anda *"jarak SL hampir tidak mengubah apa pun, RR mengubah segalanya"*.

### D. Stress biaya

| Skenario | PF | Final |
|---|---|---|
| Baseline (spread dataset ~3.4 pips) | 1.275 | $18,766 |
| +1 pip | 1.236 | $17,662 |
| +2 pips | 1.212 | $16,914 |
| +3 pips | 1.183 | $16,027 |
| **+5 pips (total ~8.4 pips = asumsi playbook)** | **1.123** | **$14,079** |

**Tetap profitable bahkan pada asumsi spread 8 pips yang Anda pakai di playbook.** Ini validasi penting: sistem Anda bekerja di asumsi biaya Anda sendiri.

---

## 4. Soal Inkonsistensi 2 vs 3 Trade/Hari

| Konfigurasi | n | PF | Final | DD% | entry/hari |
|---|---|---|---|---|---|
| **2 trade/hari (hal. 10)** | 923 | **1.275** | $18,766 | **−5.61** | 0.37 |
| 3 trade/hari (hal. 6) | 978 | 1.231 | $17,962 | −7.71 | 0.39 |
| Tanpa batas harian | 1,034 | 1.231 | $18,448 | −5.79 | 0.41 |
| Tanpa semua guardrail | 1,093 | 1.238 | $19,176 | −7.34 | 0.43 |

**Pakai angka 2 trade/hari (hal. 10).** PF tertinggi dan DD terendah. Perbaiki hal. 6 agar konsisten — dan catat bahwa dengan 2 trade/hari, eksposur harian maksimum adalah $160, bukan $250.

Menariknya, stop rugi/profit harian dan circuit breaker 2-loss **tidak pernah aktif** (hasil identik dengan/tanpa). Frekuensi 0.37/hari terlalu rendah untuk memicunya. Pertahankan sebagai jaring pengaman, tapi jangan berharap kontribusi.

---

## 5. Sensitivitas Ukuran Risiko

| Risk/trade | Final $10k | DD% |
|---|---|---|
| $50 (0.5%) | $15,479 | −4.12 |
| **$80 (0.8%)** | **$18,766** | **−5.61** |
| $160 (1.6%) | $27,532 | −10.75 |
| $500 (5%) | $57,575 | −24.66 |

PF stabil di semua level (1.275–1.279) — buktinya edge-nya nyata dan sizing hanya menskalakan. Risk $80 memberi DD −5.61% yang sangat nyaman.

**Catatan:** angka risk $500 (5%) menggoda, tapi jangan. DD −24.66% itu backtest; realitanya bisa 1.5–2× lebih dalam. Playbook Anda menetapkan 0.4% — itu pilihan yang bijak, dan saya sarankan maksimal naik ke $160 (1.6%) setelah 50 trade forward test.

---

## 6. Perbandingan Jujur vs Buy & Hold

| | Return 10 thn | Final $10k | DD |
|---|---|---|---|
| **V2 LONG-ONLY** | +87.7% | $18,766 | **−5.61%** |
| Buy & Hold emas | **+230.3%** | **$33,027** | ~−22% |
| XAU-TRV (strategi saya) | +161.8% | $26,176 | −12.13% |

**Buy & hold mengalahkan dalam return absolut.** Tapi perhatikan risikonya: V2 mencapai +87.7% dengan DD hanya **−5.61%** — itu **rasio return/DD 15.6**, jauh di atas buy & hold (~10.5) maupun XAU-TRV (13.3).

Artinya: dengan DD serendah itu, Anda punya ruang besar untuk menaikkan ukuran. Pada risk $160, hasilnya $27,532 dengan DD −10.75% — sudah mendekati XAU-TRV dengan risiko lebih kecil.

---

## 7. Kesimpulan

**Ketiga perbaikan bekerja, dan dampaknya besar:**

- PF: **0.863 → 1.275**
- $10,000: **bangkrut → $18,766**
- DD: **−100% → −5.61%**
- Entry: 0.71/hari → **0.37/hari**

**Yang paling penting:** ini konfigurasi ICT/SMC pertama yang **lolos uji kontrol entry acak** (PF +0.27 di atas acak) sekaligus konsisten IS/OOS dan tahan stress biaya. Kerangka playbook Anda + tiga koreksi arah = sistem yang punya edge terukur.

**Catatan kejujuran yang wajib:**

1. **Yang saya uji adalah kodifikasi mekanis** — sweep + displacement + FVG + bias D/H4. Komponen paling berharga di playbook Anda (skor zona 4/5, clean base, kualitas penolakan, IDM) **tidak bisa saya kuantifikasi**. Hasil live Anda akan berbeda: bisa lebih baik jika filter manual itu menyaring dengan benar, bisa lebih buruk jika eksekusi tidak disiplin.

2. **Bias long-only menangkap drift emas.** Emas naik 230% di periode ini. Uji kontrol menunjukkan edge-nya nyata di atas drift (+0.27 PF), tapi di pasar emas bearish multi-tahun, sistem ini akan jauh lebih sulit.

3. **Swap/financing belum dihitung.** Long emas kena swap negatif 2–5%/tahun di banyak broker. Dengan CAGR 6.63%, ini bisa memangkas 30–75% hasil. **Cek swap broker Anda** — ini risiko terbesar yang belum tertangkap.

4. **923 trade dalam 10 tahun** artinya butuh waktu lama untuk memvalidasi live. Dengan 1.81 trade/minggu, 50 trade ≈ 7 bulan.

**Rekomendasi:** jalankan forward test dengan konfigurasi V2 long-only, risk $80, catat setiap trade dalam R-multiple. Setelah 50 trade, bandingkan ekspektasi R aktual dengan +0.12R (ekspektasi backtest = $9.50/$80). Kalau selisihnya besar, filter manual Anda sedang menambah atau mengurangi nilai — dan itu informasi yang jauh lebih berharga dari backtest mana pun.

---

## Lampiran

| File | Isi |
|---|---|
| `reports/playbook_v2_equity.png` | Equity curve V1 vs V2 + drawdown |
| `reports/playbook_v2_trades.parquet` | 923 trade lengkap |
| `research/playbook_v2.py` | Engine backtest + definisi sinyal |
| `research/playbook_v2_report.py` | Laporan detail + uji kontrol |
| `research/playbook_v2_robust.py` | IS/OOS, sensitivitas SL/RR, stress biaya |

Reproduksi: `python research/playbook_v2_report.py && python research/playbook_v2_robust.py`
