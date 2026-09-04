# Validasi Independen: Bot Model ICAS — Uji Ulang di 10 Tahun Data

**Sumber strategi:** `github.com/Dypoi/jurnalicas` → `model_icas_bot_FIX/src/strategy/icas_strategy.py`
**Audit sebelumnya:** `LAPORAN_BACKTEST_M1_AUDIT.md` (Jan–Jun 2026, 6 bulan)
**Validasi ini:** 2016-09 → 2026-09 (**10 tahun, 20× lebih panjang**)
**Kode:** `research/icas_replicate.py`, `research/icas_control.py`

---

## Ringkasan

Saya menemukan repo `jurnalicas` di GitHub Anda — ternyata di situ sudah ada bot ICT/SMC produksi lengkap beserta **laporan audit forensik yang sangat baik**. Audit itu benar. Saya mereplikasi strateginya dari nol dan mengujinya di data 20× lebih panjang.

**Kedua temuan utama audit tersebut terkonfirmasi secara independen.**

| Temuan audit (6 bulan) | Validasi saya (10 tahun) | Status |
|---|---|---|
| Repaint level sesi menggelembungkan hasil | Kebocoran menambah **PF +0.30, net +$2,554/oz** | ✅ Terkonfirmasi |
| Data bersih → tidak ada PF > 1 | **PF 0.8803** selama 10 tahun | ✅ Terkonfirmasi |
| Sinyal ≈ entry acak | Sinyal **0.8803** vs acak **0.9957** | ✅ Terkonfirmasi (lebih buruk) |

---

## 1. Strategi yang Direplikasi

Dari `icas_strategy.py`, tanpa modifikasi logika:

```
BUY : (low[-1] ≤ SSL or low[-2] ≤ SSL)        # Judas sweep SSL
      and close > open                         # displacement bullish
      and (close > max(high[-6:-1]) or bull_FVG)   # CHoCH atau FVG
SELL: kebalikannya dengan BSL

SSL = min(asian_low, london_low)   BSL = max(asian_high, london_high)
bull_FVG : low > high[-2] + 0.30
SL $15 | TP1 $18.75 (30%) | TP2 $37.50 (25%) | TP3 $56.25 (25%) | runner 20%
STEP_SL_TO_TP1_ON_TP3 = True | Early BE+ OFF
```

Eksekusi: entry di **open bar M5 berikutnya** setelah bar sinyal tutup (bukan di bar sinyal), buy di ask, sell di bid, slippage $0.02, SL diuji sebelum TP dalam satu bar (pesimis), satu posisi pada satu waktu.

**Level sesi saya hitung secara KAUSAL** — `cummax()/cummin()` expanding dalam hari berjalan, bukan `transform('max')` seharian.

---

## 2. Hasil 10 Tahun

```
Total trades : 1,017  (0.40 per hari bursa)
Win rate     : 28.71%
Profit Factor: 0.8803
Net          : -1,155.21 USD per oz   (avg -1.1359 per trade)
t-stat       : -1.64
```

**Per tahun:**

| Tahun | n | PF | WR% | Net USD/oz |
|---|---|---|---|---|
| 2016 | 19 | 1.058 | 36.8 | +9.8 |
| 2017 | 47 | 0.640 | 36.2 | −147.3 |
| 2018 | 45 | 0.920 | 44.4 | −24.0 |
| 2019 | 56 | 0.822 | 39.3 | −79.1 |
| 2020 | 92 | 0.839 | 28.3 | −148.1 |
| **2021** | 62 | **1.708** | 41.9 | **+346.9** |
| **2022** | 68 | **1.343** | 35.3 | **+202.2** |
| 2023 | 92 | 0.638 | 23.9 | −347.6 |
| 2024 | 109 | 0.638 | 22.0 | −388.6 |
| 2025 | 193 | 0.865 | 26.4 | −252.2 |
| 2026 | 234 | 0.865 | 22.7 | −327.3 |

**Hanya 3 dari 11 tahun PF > 1.** Yang penting: 2021–2022 adalah periode emas *sideways/bearish* — di situlah sistem fade ini bekerja. Begitu emas masuk tren naik kuat (2023–2026), PF anjlok ke 0.64.

**Per sisi — ini yang paling mengungkap:**

| Sisi | n | WR% | PF | Net | t |
|---|---|---|---|---|---|
| BUY | 405 | 33.83 | **1.0977** | +356.4 | +0.77 |
| SELL | 612 | 25.33 | **0.7482** | **−1,511.6** | **−2.85** |

Sisi SELL menghancurkan akun dengan signifikansi statistik (t = −2.85). Sistem menjual setiap kali harga menyapu high sesi — di aset yang naik 230% dalam 10 tahun. Ini persis temuan Judas Swing saya di evaluasi sebelumnya: **sweep high diikuti kelanjutan naik, bukan reversal.**

---

## 3. Konfirmasi Bug Repaint F-18

Saya jalankan dua versi berdampingan — logika identik, hanya cara menghitung level sesi yang beda:

| Versi | n | WR% | PF | Net USD/oz | t |
|---|---|---|---|---|---|
| **Level KAUSAL** (benar) | 1,017 | 28.71 | **0.8803** | **−1,155.2** | −1.64 |
| **Level BOCOR** (replika bug) | 903 | 33.55 | **1.1813** | **+1,398.8** | +1.97 |
| **Selisih akibat kebocoran** | | **+4.84** | **+0.3010** | **+2,554.0** | |

Kebocoran mengubah sistem yang rugi $1,155 menjadi tampak untung $1,399 — **swing sebesar $2,554 per oz murni dari melihat masa depan.**

Audit Anda mengukur +$9,035 pada 6 bulan; saya mengukur PF +0.30 pada 10 tahun. **Arah dan magnitudo konsisten.** Diagnosis F-18 di `sessions.py` (`groupby.agg` + `merge` menempelkan agregat seharian ke setiap bar) sepenuhnya benar.

---

## 4. Uji Kontrol: Sinyal vs Entry Acak

Geometri SL/TP identik, jumlah trade sama, hanya waktu dan arah entry diacak:

| Skenario | n | WR% | PF | Net USD/oz |
|---|---|---|---|---|
| **ICAS sinyal asli** | 1,017 | 28.71 | **0.8803** | −1,155.2 |
| Acak #1 | 1,013 | 29.52 | 0.9517 | −447.8 |
| Acak #2 | 980 | 29.18 | 0.9859 | −128.8 |
| Acak #3 | 1,033 | 30.30 | 0.9706 | −273.3 |
| **Acak rata-rata 8 seed** | | | **0.9957** | |

**PF sinyal 0.8803 vs PF acak 0.9957 → selisih −0.1154.**

Sinyal `ssl_sweep + displacement` bukan hanya gagal menambah edge — ia **lebih buruk dari melempar koin**. Ini memperkuat temuan audit Anda pada konfigurasi E (sinyal 0.895 vs acak 0.912), sekarang dengan sampel 10 tahun.

Penjelasannya ada di tabel per-sisi: entry acak arahnya seimbang, sementara ICAS menghasilkan **60% sinyal SELL** (612 vs 405) di pasar yang naik terus.

---

## 5. Kesimpulan

Audit forensik di repo Anda sudah benar, dan sekarang terverifikasi di horizon 20× lebih panjang. Tidak ada yang perlu direvisi dari kesimpulannya — yang bertambah hanya keyakinan statistiknya.

**Tiga hal yang perlu ditegaskan:**

1. **Jangan jalankan bot ini dengan uang riil dalam bentuk sekarang.** PF 0.88 selama 10 tahun dengan 1,017 trade bukan hasil yang bisa diperbaiki lewat tuning parameter. Audit Anda sendiri sudah membuktikan risk 5% → bangkrut di semua konfigurasi dalam 6 bulan.

2. **Kalau tetap ingin melanjutkan, matikan sisi SELL.** Sisi BUY punya PF 1.098 (masih tipis, t=0.77 — belum signifikan, dan kemungkinan besar hanya menangkap drift emas). Sisi SELL adalah sumber kerugian dengan t = −2.85. Ini perbaikan satu baris dengan dampak terbesar.

3. **Nilai riil repo itu ada di infrastrukturnya, bukan strateginya.** Suite anti-repaint 24 uji, truncation invariance test, kontrol entry acak, verifikasi spread benar-benar dibayar — itu **engineering QA yang lebih baik dari mayoritas retail quant**. Saya menemukan look-ahead bias di kode saya sendiri minggu ini; punya harness seperti itu justru yang membedakan.

**Rekomendasi:** pertahankan infrastruktur audit itu, ganti strateginya. Pasangkan harness anti-repaint tersebut dengan XAU-TRV (Sharpe 1.00, rebalance 12×/tahun) — kombinasi engine QA yang solid dengan strategi yang tahan biaya.

---

## Lampiran

| File | Isi |
|---|---|
| `research/icas_replicate.py` | Replikasi Model ICAS + simulator multi-TP (numba) |
| `research/icas_control.py` | Uji kausal vs bocor vs acak berdampingan |
| `reports/icas_trades_10y.parquet` | 1,017 trade lengkap |

Reproduksi: `python research/icas_replicate.py && python research/icas_control.py`
