# Backtest Strategi Frekuensi Tinggi — Target ≥2 Entry/Hari

**Permintaan:** minimal 2 entry per hari (V2 sebelumnya hanya 1.81/minggu — terlalu jarang untuk dipantau)
**Modal:** $10,000 · **Periode:** 2016-09 → 2026-09 (9.8 tahun)
**Biaya:** spread bid/ask aktual dataset + slippage $0.02/oz
**Kode:** `research/hf_engine.py`, `hf_search3.py`, `hf_validate.py`

---

## JAWABAN LANGSUNG

| Metrik | **Hasil** |
|---|---|
| **Entry per hari** | **2.54** ✅ (target ≥2 tercapai) |
| **Profit Factor** | **1.203** |
| **Win rate** | **53.51%** |
| **Max Drawdown** | **−12.51%** |
| **$10,000 jadi** | **$19,881** (+98.8%, CAGR 7.25%) |
| **Total trades** | 6,405 |
| **t-stat** | +6.69 |

**Hasilnya lebih baik dari V2 low-frequency** ($19,881 vs $18,766) *dan* 6.9× lebih aktif.

---

## 1. Apa yang Berubah dari V2

Sinyal intinya **sama** (sweep BSL + displacement + bias H4). Yang berubah adalah **arsitektur eksekusi**:

| | V2 lama | **HF baru** |
|---|---|---|
| Posisi bersamaan | 1 | **8 paralel** |
| Time stop | tidak ada | **24 jam (288 bar M5)** |
| Risk per posisi | $80 | **$20** |
| Risiko total maksimum | $80 (0.8%) | $160 (1.6%) |
| Batas trade/hari | 2 | tidak dibatasi |
| Entry/hari | 0.37 | **2.54** |

**Kunci penemuannya:** V2 lama bukan kekurangan sinyal — ada 16,213 sinyal valid dalam 10 tahun (6.4/hari). Yang membatasi adalah **aturan "1 posisi pada satu waktu"**. Setiap trade menahan slot rata-rata berhari-hari, memblokir semua sinyal berikutnya.

Dengan 8 slot paralel + time-stop 24 jam, sinyal yang sama menghasilkan 6,405 trade, bukan 1,321.

**Risk per posisi diturunkan $80 → $20** agar total eksposur tetap terkendali. Ini yang menjaga DD di −12.51%; tanpa normalisasi ini (8 × $80), DD mencapai −57%.

---

## 2. Validasi

### A. Uji kontrol vs entry acak ✅

Jumlah sinyal, geometri, dan seluruh aturan risiko **identik** — hanya waktu entry diacak:

| | PF | Final |
|---|---|---|
| Acak #1 | 1.070 | $15,733 |
| Acak #2 | 1.034 | $12,840 |
| Acak #3 | 1.040 | $13,301 |
| **Acak rata-rata 8 seed** | **1.033** | **$12,718** |
| **Kandidat HF** | **1.203** | **$19,881** |
| **Selisih** | **+0.171** | **+$7,163** |

Edge-nya nyata, bukan sekadar menangkap drift emas.

### B. In-Sample / Out-of-Sample ✅

| Periode | n | /hari | WR% | PF | Final | DD% | t |
|---|---|---|---|---|---|---|---|
| **IS** 2016-09→2021-08 | 2,502 | 1.99 | 53.32 | 1.145 | $12,345 | −10.47 | +2.93 |
| **OOS** 2021-09→2026-09 | 3,903 | 3.10 | 53.63 | **1.232** | $17,537 | −13.53 | **+6.08** |

**OOS lebih baik dari IS** — kebalikan dari pola overfit.

### C. Stress biaya ✅

| Skenario | PF | Final | DD% |
|---|---|---|---|
| Baseline (~3.4 pips) | 1.203 | $19,881 | −12.51 |
| +1 pip | 1.168 | $18,273 | −14.91 |
| +2 pips | 1.138 | $16,861 | −18.15 |
| +3 pips | 1.107 | $15,360 | −21.03 |
| **+5 pips (~8.4p = asumsi playbook)** | **1.046** | **$12,338** | −29.58 |

Masih profitable di asumsi spread playbook Anda, tapi **margin-nya jauh lebih tipis** dari V2 (1.046 vs 1.123). Ini konsekuensi langsung dari frekuensi 6.9× lebih tinggi — Anda membayar spread 6.9× lebih sering.

### D. Sensitivitas parameter ✅

| SL | RR 1:1.5 | RR 1:2 | RR 1:3 |
|---|---|---|---|
| $10 | 1.130 | 1.163 | 1.192 |
| **$12** | 1.165 | **1.203** | 1.227 |
| $15 | 1.231 | 1.245 | **1.260** |

**Semua 9 kombinasi PF > 1.13.** Plateau lebar, bukan spike terisolasi.

---

## 3. Performa Tahunan

| Tahun | n | /hari | PF | WR% | P/L | Equity |
|---|---|---|---|---|---|---|
| 2016 | 14 | 0.06 | 0.12 | 14.29 | −$208 | $9,792 |
| 2017 | 574 | 2.28 | 0.96 | 51.39 | −$126 | $9,666 |
| 2018 | 371 | 1.47 | 0.86 | 51.48 | −$273 | $9,394 |
| 2019 | 528 | 2.10 | 1.36 | 54.36 | +$1,110 | $10,504 |
| 2020 | 743 | 2.95 | 1.45 | 58.55 | +$2,253 | $12,756 |
| **2021** | 450 | 1.79 | **0.83** | 44.00 | **−$635** | $12,161 |
| 2022 | 500 | 1.98 | 1.11 | 51.40 | +$484 | $12,605 |
| 2023 | 584 | 2.32 | 1.04 | 48.97 | +$191 | $12,834 |
| 2024 | 795 | 3.15 | 1.61 | 61.13 | +$3,537 | $16,334 |
| 2025 | 1,267 | 5.03 | 1.26 | 54.70 | +$2,804 | $19,175 |
| 2026 | 579 | 2.30 | 1.14 | 51.30 | +$743 | $19,881 |

**7 dari 11 tahun profit.** Tahun rugi: 2017 (−$126), 2018 (−$273), 2021 (−$635). Semuanya kecil.

Perhatikan: **frekuensi tidak stabil** — dari 1.47/hari (2018) sampai 5.03/hari (2025). Volatilitas tinggi = lebih banyak sinyal.

---

## 4. ⚠️ Peringatan Penting: Entry-nya Clustered

Ini nuansa yang harus Anda tahu sebelum menjalankan.

**"2.54 entry/hari" adalah rata-rata semua hari bursa. Realitanya tidak merata:**

| Statistik | Nilai |
|---|---|
| Hari dengan minimal 1 entry | **992 dari ~2,520 (39%)** |
| Rata-rata entry pada hari aktif | **6.46** |
| Median pada hari aktif | 7 |
| Persentil 75 | 8 |
| Persentil 90 | 11 |
| **Maksimum dalam sehari** | **37** |

Artinya: **61% hari tidak ada entry sama sekali**, lalu pada hari aktif bisa 7–11 entry sekaligus. Ini karena sinyal muncul berkelompok saat volatilitas tinggi.

**Implikasi praktis untuk Anda:**
- Kalau tujuannya "ada yang dipantau setiap hari" — ini **belum menyelesaikan** masalah itu sepenuhnya
- Kalau tujuannya "cukup aktivitas untuk terlibat" — 6.46 entry pada hari aktif sudah sangat cukup
- Anda tetap harus siap dengan hari-hari kosong

Kalau Anda ingin distribusi lebih merata, saya bisa tambahkan batas maksimum entry/hari (misal 4) — itu akan memangkas hari-hari ramai dan menaikkan PF sedikit, tapi total trade turun.

---

## 5. Perbandingan Semua Opsi

| Strategi | entry/hari | PF | WR% | Final $10k | DD% | CAGR |
|---|---|---|---|---|---|---|
| V1 playbook asli | 0.71 | 0.863 | 46.77 | **bangkrut** | −100 | — |
| V2 low-freq (1 posisi) | 0.37 | **1.275** | 54.93 | $18,766 | **−5.61** | 6.63% |
| **HF risk $20** | **2.54** | 1.203 | 53.51 | $19,881 | −12.51 | 7.25% |
| **HF risk $30** | **2.54** | 1.203 | 53.51 | **$24,822** | −16.72 | **9.68%** |
| HF risk $10 (konservatif) | 2.54 | 1.201 | 53.51 | $16,127 | −8.51 | 5.02% |
| Buy & hold emas | — | — | — | $33,027 | ~−22 | 12.7% |

**Rekomendasi saya: HF risk $20.** Keseimbangan terbaik antara frekuensi, return, dan DD. Kalau toleransi risiko Anda lebih tinggi, risk $30 memberi $24,822 dengan DD −16.72%.

---

## 6. Spesifikasi Implementasi

```
INSTRUMEN   : XAUUSD
TIMEFRAME   : M5 (sinyal), H4 (bias)

SINYAL (LONG-ONLY):
  BSL = max(asian_high, london_high)     # kausal, expanding dalam hari berjalan
  bsl_swept    = high[-1] >= BSL  OR  high[-2] >= BSL
  displacement = close > open AND (close > max(high[-6:-1]) OR bullish_FVG)
  bullish_FVG  = low > high[-2] + 0.30
  bias_bull    = close_H4 > MA240(close_H4)      # ~40 hari
  ENTRY LONG jika: bsl_swept AND displacement AND bias_bull

EKSEKUSI:
  Entry di OPEN bar M5 berikutnya (ask + $0.02 slippage)
  SL   : entry - $12.00  (120 pips)
  TP1  : entry + $12.00  -> tutup 50%, SL sisanya ke BE+ (entry + spread)
  TP2  : entry + $24.00  -> tutup sisanya (RR 1:2)
  TIME STOP: tutup di market setelah 288 bar M5 (24 jam)

MANAJEMEN POSISI:
  Maksimum 8 posisi terbuka bersamaan
  Risk $20 per posisi (0.2% dari $10k)
  Risiko total maksimum: $160 (1.6%)
  Lot = 20 / ((12.00 + spread + 0.02) x 100)
  TIDAK ADA setup SELL
```

---

## 7. Trade-off yang Harus Anda Sadari

Saya harus jujur soal apa yang dikorbankan untuk mendapat frekuensi 6.9× lebih tinggi:

| | V2 low-freq | HF |
|---|---|---|
| PF | **1.275** | 1.203 (−0.072) |
| DD | **−5.61%** | −12.51% (2.2× lebih dalam) |
| Ketahanan biaya (+5 pips) | PF **1.123** | PF 1.046 |
| Ekspektasi/trade | **$9.50** | $1.54 |
| Return/DD ratio | **15.6** | 7.9 |

**Frekuensi tinggi bukan makan siang gratis.** Anda mendapat lebih banyak aktivitas dan return absolut sedikit lebih tinggi, tapi kualitas per trade turun dan drawdown 2.2× lebih dalam.

Yang paling perlu diperhatikan: **ekspektasi per trade cuma $1.54**. Itu tipis. Kalau eksekusi live Anda punya slippage lebih buruk dari asumsi $0.02, margin ini cepat habis — lihat baris stress test +2 pips (PF turun ke 1.138).

---

## 8. Risiko yang Belum Tertangani

1. **Swap/financing.** 8 posisi long paralel yang ditahan sampai 24 jam = eksposur swap besar. Dengan swap negatif 2–5%/tahun pada notional, dan CAGR 7.25%, ini bisa memangkas **40–70% hasil**. **Ini risiko terbesar dan wajib Anda cek ke broker sebelum apa pun.**

2. **Margin requirement.** 8 posisi bersamaan pada $10k butuh margin yang tidak sedikit. Pada leverage 1:500 masih aman, tapi di 1:100 bisa terkena margin call saat semua posisi terbuka.

3. **Korelasi posisi.** 8 posisi long XAUUSD bukan diversifikasi — semuanya bergerak bersama. Saat gap turun, kedelapan kena bersamaan. DD −12.51% sudah memperhitungkan ini secara historis, tapi gap ekstrem (misal krisis) bisa lebih buruk.

4. **Bias bullish sampel.** Emas naik 230% di periode ini.

---

## 9. Rekomendasi

**Jalankan HF risk $20** kalau prioritasnya aktivitas harian. **Tetap di V2 risk $80** kalau prioritasnya kualitas dan tidur nyenyak.

Kalau saya harus memilih untuk akun sendiri: **V2 low-freq**, karena ekspektasi $9.50/trade memberi bantalan jauh lebih besar terhadap ketidaksempurnaan eksekusi live daripada $1.54.

Tapi ada argumen kuat untuk HF: **strategi yang tidak Anda pantau adalah strategi yang tidak Anda jalankan.** Kalau 1.81 entry/minggu membuat Anda kehilangan disiplin, HF yang dijalankan konsisten lebih baik daripada V2 yang ditinggalkan.

**Forward test protokol:** jalankan 3 bulan (≈150 trade pada 2.54/hari), catat setiap trade dalam R-multiple. Ekspektasi backtest = **+0.077R** ($1.54/$20). Kalau R aktual Anda di bawah +0.03R setelah 150 trade, hentikan — berarti slippage live memakan edge-nya.

---

## Lampiran

| File | Isi |
|---|---|
| `reports/hf_equity.png` | Equity curve + drawdown |
| `reports/hf_trades.parquet` | 6,405 trade lengkap |
| `research/hf_engine.py` | Engine multi-posisi paralel (numba) |
| `research/hf_search3.py` | Grid search normalisasi risiko |
| `research/hf_validate.py` | Uji kontrol, IS/OOS, stress biaya |

Reproduksi: `python research/hf_validate.py`
