# Backtest Terisolasi: Januari – Agustus 2026

Periode 8 bulan terakhir dalam dataset — data paling baru, paling relevan dengan
kondisi yang akan Anda hadapi.

> Catatan metode: backtest tetap dijalankan penuh dari 2016 lalu trade diiris per
> `entry_time`. Kalau langsung memotong data di Januari 2026, MA240 H4 (butuh 40 hari
> warmup) akan NaN dan hasilnya palsu.

---

## Hasil utama

| Metrik | Full 2016–2026 | **Jan–Ags 2026** |
|---|---|---|
| Trades | 6.274 | **529** |
| Frekuensi | 2,45/hari | **3,12/hari** |
| Win rate | 53,70% | **52,36%** |
| Profit Factor | 1,213 | **1,166** |
| Net | +$12.567 | **+$1.006** |
| Ekspektasi | +0,100R | **+0,095R** |
| Max Drawdown | −14,47% | **−5,32%** |
| t-stat | +6,89 | **+1,67** |

**Tetap profitabel, dan ekspektasinya konsisten** (+0,095R vs +0,100R jangka panjang).
Drawdown justru jauh lebih dangkal.

Tapi **t-stat +1,67 di bawah ambang signifikansi 2,0**. Dengan 529 trade dalam 8 bulan,
hasil +$1.006 belum bisa dibedakan dari keberuntungan. Ini bukan kegagalan — ini
konsekuensi matematis dari edge tipis pada sampel pendek.

---

## Rincian bulanan — dan tiga bulan yang hilang

| Bulan | n | WR | PF | Net | Bias H4 bull | Harga emas |
|---|---|---|---|---|---|---|
| Jan | 173 | 56,6% | 1,480 | **+$866** | 100% | 4327→4896 (+13,1%) |
| Feb | 130 | 50,0% | 1,082 | +$128 | 100% | 4824→5279 (+9,4%) |
| Mar | 33 | 45,5% | 0,820 | −$78 | 43,5% | 5338→4697 (**−12,0%**) |
| **Apr** | **0** | — | — | **$0** | **0%** | 4699→4627 (−1,5%) |
| Mei | 25 | 64,0% | 2,014 | +$219 | 27,1% | 4628→4540 (−1,9%) |
| **Jun** | **0** | — | — | **$0** | **0%** | 4545→4006 (**−11,9%**) |
| **Jul** | **0** | — | — | **$0** | **0%** | 4007→4047 (+1,0%) |
| Ags | 168 | 49,4% | 0,937 | −$129 | 90,1% | 4076→4452 (+9,2%) |

**April, Juni, dan Juli nol trade.** Penyebabnya bukan kelangkaan sinyal — sweep BSL
tetap terjadi 9–18% dan displacement 13–15%. Penyebabnya **filter bias H4 = 0%**:
harga berada di bawah MA240 H4, sehingga sistem mematikan diri sepenuhnya.

---

## Ini justru bukti filter H4 bekerja

Juni 2026 emas turun **−11,9%**. Sistem long-only yang tetap masuk di bulan itu akan
babak belur. Filter menahannya.

Saya uji langsung dengan mematikan filter H4:

| Konfigurasi | Hasil 10 tahun |
|---|---|
| **Dengan filter H4** (sistem asli) | 6.274 trade, PF **1,213**, bertahan sampai 2026 |
| **Tanpa filter H4** | 1.849 trade, PF **0,871**, **KILL-SWITCH kena** — sistem mati Mei 2019 |

Tanpa filter, sistem tidak bertahan hidup sampai 2026. Ia bangkrut tujuh tahun lebih awal.

Di periode gold turun (Mar–Jul 2026), sistem asli tetap **PF 1,218 dari 58 trade** —
sedikit tapi positif.

---

## Yang perlu Anda siapkan mental untuk jurnal 5 hari

1. **Nol trade selama berhari-hari adalah perilaku normal, bukan kerusakan.**
   Tiga bulan penuh di 2026 tidak menghasilkan satu pun entry. Kalau dashboard Anda
   diam beberapa hari, kemungkinan besar bias H4 sedang bearish — sistem sedang
   melindungi Anda, bukan rusak.

2. **Frekuensi sangat tidak merata.** Januari 173 trade, April 0. Rata-rata "2,54/hari"
   adalah angka jangka panjang, bukan janji harian.

3. **Bulan bagus dan buruk bergantian.** Jan PF 1,480 · Mar 0,820 · Mei 2,014 · Ags 0,937.
   Delapan bulan saja tidak cukup untuk menilai; lima hari jelas tidak.

4. **Agustus 2026 rugi tipis** (−$129, PF 0,937) meski emas naik +9,2%. Sistem bisa
   kalah bahkan di bulan bullish.

---

## Kesimpulan jujur

Periode terbaru **mengonfirmasi sistem masih hidup**: ekspektasi +0,095R hampir identik
dengan +0,100R jangka panjang, dan drawdown lebih dangkal (−5,32%).

Tapi t-stat +1,67 mengingatkan hal yang sama seperti sebelumnya — pada sampel pendek,
sistem ini tidak bisa membuktikan dirinya. Yang bisa disimpulkan hanyalah: **tidak ada
tanda kerusakan pada data terbaru.**
