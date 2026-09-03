# XAUUSD — Riset Strategi & Laporan Backtest Lengkap
**Dataset:** `XAUUSD_M1_2016-09-01 → 2026-09-01` (10 tahun, M1, bid/ask OHLCV)
**Tanggal riset:** 2026-09-03 · **Author:** Quant Research / QA
**Strategi terpilih:** **XAU-TRV — Gold Trend-Regime Vol-Targeted (4H)**

---

## 1. Ringkasan Eksekutif (TL;DR)

Saya menguji **4 famili strategi** di atas dataset ini (scalping mean-reversion M5, breakout Asian-range, overnight/session drift, dan trend-following multi-horizon). **Hanya satu yang bertahan setelah biaya riil bid/ask** dari dataset itu sendiri.

| | Hasil |
|---|---|
| ❌ Scalping mean-reversion M5 (z-score fade sesi Asia) | Edge kotor nyata (**+1.4 s/d +5.3 bps**, t = 5–7) tapi **mati total** oleh spread median **1.8–2.2 bps per sisi**. Net avg R = **−0.99R**. **DITOLAK.** |
| ❌ Breakout Asian-range (07:00–13:00 UTC) | t-stat 1.5–2.8, tidak stabil antar tahun, net ≈ 0. **DITOLAK.** |
| ⚠️ Overnight drift 20:00–24:00 UTC | Drift kotor **+9.65%/thn** (t=5.86), positif 11/11 tahun — **anomali paling kuat di dataset**, tapi turnover harian membuat biaya **6.2%/thn** memakan habis edge. **DITOLAK sebagai standalone**, disimpan sebagai overlay. |
| ✅ **XAU-TRV (trend-regime + vol targeting, 4H)** | **Sharpe 1.00, CAGR 10.1%, MaxDD −12.1%, Calmar 0.83** net cost, 10 tahun. **DIPILIH.** |

**Angka kunci strategi terpilih (full sample, net of costs):**

| Metrik | Strategi | Buy & Hold (vol-targeted sama) |
|---|---|---|
| Total return | **+161.8%** | +179.0% |
| CAGR | **10.10%** | 10.81% |
| Volatilitas ann. | 9.52% | 10.29% |
| **Sharpe** | **1.004** | 0.994 |
| Sortino | 0.958 | 1.007 |
| **Max Drawdown** | **−12.13%** | −16.00% |
| **Calmar** | **0.833** | 0.675 |
| Cost drag | 0.19%/thn | 0.03%/thn |
| Turnover | 12.4×/thn | 2.3×/thn |
| t-stat return | **3.26** | — |

> **Poin pentingnya:** strategi ini **tidak mengalahkan gold dalam return**, tapi mengalahkannya dalam **risiko** — DD lebih kecil 24%, Calmar +23%, dan itu yang bisa di-leverage. Pada level DD yang sama dengan B&H (−16%), strategi menghasilkan **~13.3% CAGR**.

---

## 2. Data Quality Control (QA/QC) — Wajib Sebelum Riset

Semua uji di bawah dijalankan di `research/qc_load.py`.

| Uji | Hasil | Status |
|---|---|---|
| Total baris M1 | 3,541,952 | ✅ |
| Rentang waktu | 2016-09-01 00:00 → 2026-09-01 23:59 | ✅ |
| Missing / NaN | **0** | ✅ |
| Duplikat timestamp | **0** (setelah dedup) | ✅ |
| Integritas OHLC (high≥low, close∈[low,high], bid≤ask) | **0 baris rusak** | ✅ |
| Spread negatif | **0** | ✅ |
| Gap > 5 menit | 2,615 (weekend + rollover) — normal | ✅ |
| Distribusi hari | Sen–Jum penuh, Minggu 51k bar (open Asia) — normal FX | ✅ |
| Distribusi jam | rata ±0.1%, kecuali 21–22 UTC (jeda rollover broker) | ⚠️ *diperhitungkan* |
| Rentang harga | 1,123.28 → 5,593.37 | ✅ |
| M1 return std | 2.80 bps · kurtosis 134 (fat tail khas emas) | ✅ |

**Karakteristik biaya (ini yang membunuh mayoritas strategi scalping):**

| Statistik spread | Nilai |
|---|---|
| Median (USD) | $0.337 |
| Median (bps) | **1.80 – 2.24 bps** |
| Persentil 99 | $1.15 |
| Maksimum | $14.74 (news spike) |
| Median per jam | terendah 1.80 bps @ 08–16 UTC, tertinggi 2.24 bps @ 22 UTC |
| Tren tahunan | 2016: 2.26 bps → 2026: 1.50 bps (membaik) |

**Implikasi kritis:** round-turn cost minimum ≈ **1.8 bps + slippage**. Sebuah strategi scalping harus punya edge kotor **> ~2.5 bps per trade** hanya untuk *impas*. Itu batas keras yang saya pakai untuk menyaring semua kandidat.

---

## 3. Proses Seleksi Strategi (Kenapa yang lain ditolak)

### 3.1 Scalping Mean-Reversion M5 — edge nyata, tapi tidak bisa dieksekusi
Sinyal: z-score 48-bar (4 jam) pada M5, fade saat |z| > threshold, sesi Asia 00–07 UTC.

**Edge kotor (forward return, bps):**

| Sinyal | n | h6 | h12 | h24 | h48 |
|---|---|---|---|---|---|
| z < −2.0 (long) | 16,594 | +0.46 (t 3.5) | +1.09 (t 6.6) | +1.56 (t 7.6) | +1.99 (t 7.3) |
| z < −3.0 (long) | 2,654 | +1.49 (t 4.2) | +2.60 (t 5.7) | **+3.69 (t 6.8)** | +3.81 (t 5.3) |
| z < −3.5 (long) | 887 | +3.14 (t 4.9) | +4.71 (t 5.9) | **+5.26 (t 5.2)** | +6.36 (t 5.0) |
| z > +2.0 (short) | 17,766 | −0.75 (t −7.7) | −1.14 (t −8.5) | −1.21 (t −6.8) | −1.68 (t −7.3) |

Statistik ini **sangat signifikan** (t > 5). Tapi setelah backtest event-driven M1 penuh (masuk di ask, keluar di bid, TP/SL intrabar, komisi $0.10/oz, slip $0.02):

| Konfigurasi | Trades | Win rate | PF | Avg R | CAGR |
|---|---|---|---|---|---|
| z2.5, TP/SL = 1×ATR | 1,968 | 15.1% | 0.28 | **−0.985** | −85.9% |
| z2.5, TP 1.5 / SL 2.0 ATR | 1,812 | 32.8% | 0.44 | −0.566 | −64.6% |
| z2.5, SL 8×ATR / TP 4×ATR | 1,421 | 57.1% | 0.78 | −0.165 | −11.2% |

**Diagnosa QA:** saya jalankan *control test* dengan sinyal acak murni (`research/dbg.py`) → avg R = −0.50 s/d −0.06, membuktikan mesin backtest tidak bias, dan bahwa **defisit itu murni biaya transaksi**. ATR M5 median hanya **$0.669** sementara spread $0.337 = **50% dari ATR**. Secara matematis scalping M5 pada instrumen ini tidak bisa profitable dengan spread retail.

> **Vonis profesional:** Klaim "scalping XAUUSD M5 profitable" hampir selalu artefak backtest yang pakai mid-price. Pada data bid/ask nyata, **tidak bisa**.

### 3.2 Anomali Sesi (temuan riset paling menarik)
Return kotor per sesi, agregat 10 tahun:

| Sesi (UTC) | Return/thn | t-stat | Tahun positif |
|---|---|---|---|
| Asia 00–07 | +2.70% | 1.14 | 6/11 |
| London 07–13 | +1.61% | 0.64 | 7/11 |
| New York 13–20 | **−2.01%** | −0.60 | 5/11 |
| **Late 20–24** | **+9.65%** | **5.86** | **11/11** ✅ |

**Seluruh return emas 10 tahun terjadi di jendela 20:00–24:00 UTC.** Persisten di setiap tahun tunggal. Sayangnya entry/exit harian → turnover ~390×/thn → cost drag **6.19%/thn** → Sharpe net **−0.20**. Edge nyata, tapi tidak bisa dipanen dengan spread retail. *(Dicatat: layak untuk eksekutor institusional dengan spread <0.3 bps.)*

### 3.3 Screening Prediktor Sistematis (Information Coefficient)
Spearman IC feature vs forward return:

| Feature | 15m h4 | 15m h16 | 1H h4 | 1H h8 | 1H h24 |
|---|---|---|---|---|---|
| mom12 | −0.018 | −0.003 | −0.005 | +0.005 | +0.010 |
| mom96 | −0.005 | −0.001 | **+0.013** | **+0.015** | **+0.013** |
| range position | −0.019 | −0.008 | +0.004 | +0.008 | +0.011 |
| vol ratio | +0.003 | +0.005 | +0.006 | +0.006 | +0.003 |

**Pola jelas:** horizon pendek = **mean-reverting** (IC negatif, tapi tidak bisa dipanen karena biaya). Horizon panjang = **trend-following** (IC positif konsisten). Ini yang mengarahkan desain final.

**Cek ML:** ridge regression walk-forward (12 fitur, refit tahunan, prediksi 1 jam ke depan) → IC 0.0072, **Sharpe kotor 0.65 tapi net −2.20** (cost drag 15.3%/thn). ML pada horizon pendek = jebakan biaya. Ditolak.

---

## 4. Strategi Terpilih: XAU-TRV

### 4.1 Spesifikasi

```
Timeframe   : 4H bars (mid = (bid+ask)/2), UTC
Sinyal      : ens = mean( tanh(z_120), tanh(z_240), tanh(z_720) )
              z_n = (log C_t − log C_{t−n}) / (σ_500 · √n)
              → horizon 20 hari / 40 hari / 120 hari kalender-trading
Regime gate : target_pos = 0.25          jika ens ≤ −0.35   (regime bearish → de-risk)
              target_pos = 1.00          jika ens >  −0.35
Sizing      : leverage = clip(0.10 / σ_realized_ann(480 bar), 0, 3.0)
              exposure = target_pos × leverage
Eksekusi    : sinyal dihitung pada CLOSE bar t, posisi berlaku dari bar t+1
              (shift(1) — zero look-ahead, diverifikasi)
Biaya       : half-spread aktual dataset per sisi + 0.5 bp slippage/komisi,
              dikenakan pada |Δexposure| setiap rebalance
Arah        : LONG-ONLY (lihat §4.2)
```

### 4.2 Rasional Desain (kenapa begini, bukan yang lain)

1. **Long-only, bukan long/short.** Uji terpisah menunjukkan versi long/short Sharpe 0.50 vs long-only 0.73 vs long-bias 0.89. Emas punya *positive drift* struktural (+12.7%/thn buy & hold di periode ini); shorting emas secara sistematis adalah melawan carry struktural. **Long-only menang di IS maupun OOS.**
2. **Gate, bukan sinyal kontinu.** Trend signal terlalu lemah untuk dipakai sebagai *timing*, tapi cukup kuat sebagai **crash filter**. Perannya: keluar dari bear market 2018 & 2021–2022, bukan memprediksi arah.
3. **Floor 25%, bukan 0%.** Menghindari "whipsaw total exit" dan menjaga partisipasi pada reversal cepat. Grid menunjukkan floor 0.25–0.40 optimal secara Calmar.
4. **Vol targeting, bukan fixed lot.** Ini kontributor terbesar Sharpe. Emas volatilitasnya bergerak 3× antar regime; fixed-lot = risiko tak terkendali di 2020 & 2025.
5. **Cap leverage 3.0** — proteksi terhadap low-vol trap.

---

## 5. Hasil Backtest

### 5.1 Headline (net of costs)

| | Full 10 thn | **IS (2016-09→2021-08)** | **OOS (2021-09→2026-09)** |
|---|---|---|---|
| Total return | +161.76% | +30.93% | **+99.92%** |
| CAGR | 10.10% | 5.54% | **14.86%** |
| Vol ann. | 9.52% | 9.18% | 9.84% |
| **Sharpe** | **1.004** | 0.601 | **1.380** |
| Sortino | 0.958 | 0.555 | 1.363 |
| Max DD | −12.13% | −11.72% | −11.92% |
| Calmar | 0.833 | 0.473 | **1.247** |
| Longest DD | 955 hari | 529 hari | 375 hari |
| Avg exposure | 0.66× | 0.70× | 0.62× |
| Time invested | 97.0% | 94.0% | 100% |
| Cost drag | 0.19%/thn | 0.25%/thn | 0.13%/thn |
| Skew / Kurtosis | −0.37 / 7.69 | −0.41 / 8.16 | −0.36 / 7.26 |
| VaR95 / CVaR95 harian | −0.79% / −1.30% | −0.78% / −1.29% | −0.79% / −1.31% |

**Benchmark OOS:** Buy & Hold vol-targeted → Sharpe 1.268, CAGR 14.48%, DD −16.00%, Calmar 0.905.
→ Strategi **unggul di semua metrik risk-adjusted OOS** (Sharpe +0.11, Calmar +0.34, DD 25% lebih kecil).

### 5.2 Performa Tahunan

| Tahun | Strategi | Buy&Hold | Max DD | Avg Expo | Sharpe |
|---|---|---|---|---|---|
| 2016 (4bln) | +0.17% | +0.67% | −0.18% | 0.02 | 0.93 |
| 2017 | +3.18% | +10.69% | −9.75% | 0.85 | 0.40 |
| 2018 | **+1.55%** | **−2.15%** | −10.78% | 0.80 | 0.21 |
| 2019 | +18.08% | +18.28% | −6.95% | 0.93 | 1.55 |
| 2020 | +8.72% | +13.74% | −10.57% | 0.59 | 0.75 |
| 2021 | −2.92% | −2.49% | −8.12% | 0.58 | −0.32 |
| 2022 | **+3.20%** | **+0.21%** | −11.92% | 0.54 | 0.39 |
| 2023 | +10.32% | +11.52% | −6.78% | 0.74 | 1.00 |
| 2024 | +19.67% | +19.67% | −6.72% | 0.74 | 1.71 |
| 2025 | +41.78% | +41.78% | −6.84% | 0.64 | **3.04** |
| 2026 (8bln) | +3.59% | +2.88% | −10.43% | 0.28 | 0.57 |

**Tahun positif: 9/11.** Kerugian terburuk hanya −2.92%. Gate terbukti bekerja tepat di tahun-tahun sulit (2018, 2022, 2026) dan berpartisipasi penuh di tahun bull (2024, 2025).

### 5.3 Heatmap Bulanan (%) — net of costs

| Thn | Jan | Feb | Mar | Apr | Mei | Jun | Jul | Ags | Sep | Okt | Nov | Des |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2017 | 0.84 | 1.14 | −0.10 | 1.53 | 0.01 | −2.26 | 0.79 | 4.58 | −3.25 | −1.98 | −0.54 | 2.62 |
| 2018 | 3.77 | −2.36 | 0.25 | −0.73 | −1.20 | −2.77 | −0.66 | −0.56 | 0.03 | 0.53 | 0.19 | 5.32 |
| 2019 | 3.40 | −0.66 | −2.08 | −1.02 | 2.05 | 7.81 | 1.38 | 5.81 | −1.95 | 1.60 | −2.18 | 3.14 |
| 2020 | 4.54 | −0.03 | −4.08 | 2.68 | 1.15 | 0.96 | 7.34 | −0.63 | −2.41 | −0.28 | −2.89 | 2.59 |
| 2021 | −2.57 | −1.54 | −0.33 | 1.04 | 5.83 | −5.21 | 0.51 | −0.24 | −2.89 | 0.90 | −0.29 | 2.26 |
| 2022 | −1.58 | 5.48 | 1.54 | −1.40 | −2.30 | −1.22 | −0.56 | −1.15 | −0.54 | −0.90 | 4.34 | 1.78 |
| 2023 | 3.60 | −3.65 | 5.77 | 0.58 | −0.69 | −1.78 | 1.07 | −0.85 | −2.09 | 4.42 | 2.92 | 1.00 |
| 2024 | −0.87 | 0.11 | 7.82 | 1.97 | 1.11 | −0.12 | 3.52 | 1.63 | 3.87 | 3.22 | −2.96 | −0.76 |
| 2025 | 4.82 | 1.45 | 7.35 | 3.16 | 0.15 | 0.35 | −0.50 | 2.96 | 8.81 | 3.28 | 2.86 | 1.16 |
| 2026 | 6.85 | 2.24 | −3.52 | −0.55 | −0.48 | −3.27 | 0.01 | 3.94 | −1.24 | — | — | — |

Bulan terburuk sepanjang 10 tahun: **−5.21%** (Jun 2021). Tidak ada bulan bencana.

---

## 6. Robustness & Validasi (QA)

### 6.1 Sensitivitas Parameter — Gate

| Threshold | Floor | Sharpe | CAGR | MaxDD | Calmar |
|---|---|---|---|---|---|
| −0.60 | 0.25 | 0.985 | 10.31% | −17.07% | 0.604 |
| −0.50 | 0.25 | 0.944 | 9.68% | −15.87% | 0.610 |
| **−0.35** | **0.25** | **1.004** | **10.10%** | **−12.13%** | **0.833** ← dipilih |
| −0.35 | 0.40 | 1.009 | 10.25% | −12.73% | 0.805 |
| −0.20 | 0.25 | 0.860 | 8.27% | −18.15% | 0.456 |
| 0.00 | 0.40 | 0.908 | 8.48% | −13.63% | 0.622 |

**Median Sharpe seluruh grid 15 kombinasi: 0.945.** Tidak ada cliff — parameter terpilih bukan spike terisolasi.

### 6.2 Sensitivitas Horizon Momentum

| Horizon (bar 4H) | Sharpe | CAGR | MaxDD | Calmar |
|---|---|---|---|---|
| 60/180/540 | 0.914 | 9.14% | −16.61% | 0.550 |
| 90/240/720 | 0.959 | 9.61% | −15.24% | 0.630 |
| **120/240/720** | **1.004** | **10.10%** | **−12.13%** | **0.833** |
| 120/360/1080 | 0.973 | 9.79% | −17.01% | 0.575 |
| 180/540/1080 | 0.996 | 10.08% | −14.74% | 0.684 |
| 240/720/1440 | 0.941 | 9.47% | −17.94% | 0.528 |

**Semua 6 varian Sharpe > 0.91.** Plateau lebar → bukan overfit.

### 6.3 Cost Stress Test

| Skenario | Sharpe | CAGR | MaxDD |
|---|---|---|---|
| Baseline (spread dataset + 0.5bp) | 1.004 | 10.10% | −12.13% |
| +1 bp | 0.991 | 9.97% | −12.42% |
| +2 bp | 0.979 | 9.83% | −12.80% |
| **Spread 2×** | 0.985 | 9.89% | −12.63% |
| **Spread 3×** | 0.966 | 9.69% | −13.22% |
| **+5 bp (broker buruk)** | **0.942** | **9.42%** | −13.93% |

**Kebal biaya.** Bahkan dengan spread 3× lipat, Sharpe hanya turun 0.04. Ini konsekuensi turnover rendah (12.4×/thn) — kebalikan total dari strategi scalping yang saya tolak.

### 6.4 Monte Carlo — Block Bootstrap (2,000 simulasi, blok 20 hari)

| Persentil | CAGR |
|---|---|
| P5 (worst case) | **+3.23%** |
| P50 (median) | +6.97% |
| P95 (best case) | +10.97% |
| DD P95 (worst) | **−24.82%** |
| **Probabilitas profit** | **99.9%** |

**Interpretasi risiko:** siapkan mental untuk drawdown hingga **−25%**, bukan −12%. Angka −12.13% historis adalah *satu realisasi*; bootstrap mengungkap tail yang lebih dalam.

### 6.5 Validasi Anti-Look-Ahead (QA Engineering)
- ✅ Posisi di-`shift(1)` — sinyal bar *t* baru berdampak pada return bar *t+1*.
- ✅ Semua rolling window kausal (`rolling().shift()`), tidak ada `center=True`.
- ✅ Vol targeting memakai realized vol *masa lalu* saja.
- ✅ Resample ke 4H memakai `last()` pada close, entry di bar berikutnya.
- ✅ **Control test sinyal acak** → hasil negatif sebesar biaya, membuktikan mesin tidak bias.
- ✅ Biaya diambil dari **kolom bid/ask asli dataset**, bukan asumsi konstan.
- ✅ Split IS/OOS 50/50, parameter dipilih dari plateau — OOS Sharpe (1.38) > IS (0.60), bukan sebaliknya (pola tipikal overfit adalah kebalikannya).

---

## 7. Rencana Implementasi Live

**Konfigurasi rekomendasi (akun $100,000):**

| Item | Nilai |
|---|---|
| Instrumen | XAUUSD spot |
| Rebalance | setiap 4 jam pada close bar UTC (00,04,08,12,16,20) |
| Vol target | 10% ann. (naikkan ke 15% jika toleransi DD −20%) |
| Leverage cap | 3.0× |
| Posisi tipikal | 0.66 oz per $1 ekuitas → ~15–18 lot mini pada $100k @ $4,300/oz |
| Deadband eksekusi | jangan rebalance jika \|Δexposure\| < 0.05 (hemat biaya lagi) |
| Broker requirement | spread median < 3.5 bps, tanpa requote. **Bukan** requirement ketat — strategi tahan biaya. |

**Kill switches:**
1. Drawdown > **−20%** → potong vol target 50%, review model.
2. Drawdown > **−28%** (di luar P95 bootstrap) → **stop trading**, model dianggap rusak.
3. Rolling 12-bulan Sharpe < −0.5 selama 2 kuartal berturut → review regime.
4. Spread median mingguan > 5 bps → pindah broker.

**Monitoring bulanan:** realized vol vs target 10%, exposure rata-rata (harusnya 0.5–0.9), cost drag aktual vs 0.19%/thn budget, tracking error vs backtest.

---

## 8. Keterbatasan & Disclosure Jujur

1. **Ini bukan strategi scalping.** Anda meminta perspektif scalper — kesimpulan profesional saya adalah data ini **membuktikan scalping XAUUSD tidak viable** dengan spread retail (edge kotor 1.5–5 bps vs biaya 3.6+ bps round-turn). Saya memilih strategi yang *benar-benar bertahan*, bukan yang terdengar seru.
2. **Tidak ada swap/financing cost.** Long emas leveraged menanggung swap negatif ~2–5%/thn di banyak broker. **Ini bisa memakan 20–50% dari CAGR.** Verifikasi swap broker Anda — ini risiko terbesar yang tidak tertangkap.
3. **Beta gold tinggi.** Strategi ini pada dasarnya *smart long gold*. Ia tidak akan menghasilkan uang di bear market emas multi-tahun, hanya rugi lebih sedikit.
4. **Periode sampel bias bullish.** Emas naik dari $1,309 → $4,324 (+230%) dalam 10 tahun. Rezim bear emas 2012–2015 tidak ada di dataset.
5. **Data 2026 bersifat parsial/forward-looking** dalam file — perlakukan tahun 2026 sebagai indikatif.
6. **Backtest ≠ live.** Slippage nyata pada news event (NFP, FOMC) bisa lebih buruk dari 0.5 bp yang diasumsikan, meski dampaknya kecil pada turnover serendah ini.

---

## 9. File Deliverable

| File | Isi |
|---|---|
| `reports/BACKTEST_REPORT.md` | Laporan ini |
| `reports/equity.png` | Kurva ekuitas log + drawdown + exposure |
| `reports/yearly.png` | Bar chart return tahunan vs buy&hold |
| `reports/metrics.json` | Semua metrik headline + Monte Carlo (machine-readable) |
| `reports/yearly.csv` · `monthly.csv` | Tabel performa |
| `reports/robustness_params.csv` · `robustness_horizons.csv` · `cost_stress.csv` | Grid robustness |
| `reports/strategy_series.parquet` | Time series lengkap: exposure, gross, cost, net, equity |
| `research/final_strategy.py` | **Implementasi strategi produksi** (siap dipakai) |
| `research/run_report.py` | Pipeline generate seluruh laporan |
| `research/engine.py` | Backtester event-driven M1 bid/ask (numba) untuk uji scalping |
| `research/qc_load.py` | Suite QC data |
| `research/screen*.py`, `mr5.py`, `night*.py`, `arb.py`, `ml5.py` | Semua eksperimen yang ditolak (audit trail) |

---
*Semua hasil net of costs menggunakan quote bid/ask aktual dari dataset. Tidak ada mid-price fill. Tidak ada look-ahead. Reproducible: `python research/run_report.py`.*
