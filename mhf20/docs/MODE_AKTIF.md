# Mode Aktif — Maksimal 5 Entry Per Hari

Sesuai permintaan: cap dinaikkan dari 1 ke **5 entry/hari**. Sudah aktif sebagai default.

Ini pilihan yang lebih cocok dengan sifat sistem, karena sinyal MHF-20 memang
**menggerombol** — dan cap 1/hari membuang terlalu banyak sinyal bagus di hari ramai.

---

## Perbandingan tiga mode

| | Standar | Santai (1/hari) | **Aktif (5/hari)** |
|---|---|---|---|
| Cap harian | tanpa batas | 1 | **5** |
| Entry/hari nyata | 2,03 | 0,31 | **1,15** |
| Total trade | 4.905 | 740 | **2.779** |
| Risiko/trade | $20 | $100 | **$40** |
| Slot | 8 | 2 | **8** |
| Risiko maks terbuka | $160 | $200 | **$320** |
| Win rate | 55,33% | 55,27% | **55,70%** |
| Profit Factor | 1,304 | 1,362 | **1,353** |
| Equity 10 thn | $23.881 | $19.482 | **$23.061** |
| CAGR | 9,50% | 7,20% | **9,10%** |
| Max Drawdown | −11,68% | −10,43% | **−11,83%** |
| t-stat | +8,43 | +3,77 | **+7,16** |

Mode aktif hampir menyamai CAGR mode standar (9,10% vs 9,50%) dengan **43% lebih sedikit
trade**, dan PF-nya lebih tinggi (1,353 vs 1,304). Bukti statistiknya juga jauh lebih kuat
dari mode santai (t +7,16 vs +3,77).

---

## Tetap perlu Anda tahu: 75% hari tidak ada sinyal

Cap 5/hari **tidak** berarti 5 trade tiap hari. Rata-rata nyatanya **1,15/hari**.

Sebaran dari 3.110 hari:

| Entry dalam sehari | Jumlah hari |
|---|---|
| 0 (tidak ada sinyal) | **2.337 hari (75%)** |
| 1 | 162 |
| 2 | 81 |
| 3 | 76 |
| 4 | 43 |
| **5 (cap tercapai)** | **411** |

Polanya: kalau ada sinyal, biasanya banyak sekaligus (411 hari langsung mentok cap 5).
Kalau sepi, kosong total. Jadi harapkan **hari-hari kosong beruntun, lalu hari ramai
dengan 5 trade**.

Inilah alasan cap 5 lebih baik dari cap 1 untuk sistem ini: ia menangkap hari-hari ramai
yang produktif, tanpa membiarkan risiko lepas kendali.

---

## Validasi

| Periode | n | WR | PF | Net |
|---|---|---|---|---|
| IS (2016→2023/02) | 1.465 | 55,4% | **1,382** | +$6.376 |
| OOS (2023/03→2026) | 1.314 | 56,0% | **1,330** | +$6.684 |
| Jan–Ags 2026 | 186 | 49,5% | **0,961** | **−$131** |

IS dan OOS keduanya kuat dan seimbang. **Tapi 2026 rugi tipis** (PF 0,961) — sama seperti
mode lain, delapan bulan terakhir memang datar. Jangan kaget kalau 5 hari pertama merah.

**Ketahanan biaya:**

| Slippage tambahan | PF |
|---|---|
| +$0,00 | 1,353 |
| +$0,20 | 1,290 |
| +$0,50 | **1,171** |

Masih sehat di +$0,50/sisi. Ini penting karena swap belum dimodelkan.

---

## Bug yang ditemukan saat mengerjakan ini

Saat memverifikasi cap benar-benar bekerja, saya menemukan **hari dengan 6 entry padahal
cap-nya 5**.

Penyebabnya: penghitung dikunci ke hari **sinyal** (`day[i]`), padahal entry dieksekusi di
bar berikutnya (`j = i+1`). Sinyal di bar terakhir suatu hari menghasilkan entry yang jatuh
di hari berikutnya, tapi tetap dihitung ke hari lama — sehingga hari baru bisa kelebihan
jatah.

Sudah diperbaiki: penghitung kini dikunci ke **hari eksekusi** (`day[j]`), persis seperti
yang dilihat broker. Setelah perbaikan: maksimum 5/hari, nol pelanggaran.

Bug ini tidak akan ketahuan tanpa memeriksa sebaran per hari — angka agregat terlihat
normal. Ini alasan saya selalu memverifikasi guard baru benar-benar mengikat.

---

## Setelan

```python
MODE                = "aktif"
MAX_ENTRIES_PER_DAY = 5
RISK_PER_POSITION   = 40.0     # $36,84 nyata setelah pembulatan lot
MAX_CONCURRENT      = 8
BIAS_MIN_DIST_PCT   = 1.50
MAX_ORDERS_PER_DAY  = 6        # rem keras
```

### Catatan pembulatan lot

XAUUSDm minimum 0,01 lot, jadi risiko tidak bisa presisi:

| Setelan | Lot | Risiko nyata |
|---|---|---|
| $20 | 0,02 | $24,56 |
| $30 | 0,02 | $24,56 ← sama dengan $20 |
| **$40** | **0,03** | **$36,84** |
| $50 | 0,04 | $49,12 |

Menyetel $30 tidak ada gunanya — hasilnya identik dengan $20. Saya pilih $40 karena
menghasilkan lot 0,03 yang berbeda nyata.

### Ganti mode

Ubah di `mhf20/live/config.py` **dan** `mhf20/strategy.py` (nilai wajib sama):

| | Aktif | Santai | Standar |
|---|---|---|---|
| `MAX_ENTRIES_PER_DAY` | 5 | 1 | 0 |
| `RISK_PER_POSITION` | 40.0 | 100.0 | 20.0 |
| `MAX_CONCURRENT` | 8 | 2 | 8 |
| `BIAS_MIN_DIST_PCT` | 1.50 | 1.50 | 0.50 |
| `MAX_ORDERS_PER_DAY` | 6 | 2 | 12 |

---

## Penegakan live

`executor.py` menolak order ke-6 di hari yang sama:

> `Batas 5 entry/hari sudah terpakai (5). Menunggu besok.`

Tes **[24]** memaksa `MAX_ENTRIES_PER_DAY`, `MAX_CONCURRENT`, dan `RISK_PER_POSITION`
identik antara backtest dan live, plus memverifikasi cap dikunci ke hari eksekusi.

**Audit: paritas 191/191 · resilience 78/78 · eksekusi 38/38.**

---

## Risiko

Risiko maksimum terbuka naik ke **$320 (3,2% akun)** — tertinggi dari ketiga mode. Dengan
411 hari yang mentok cap 5, akan ada hari di mana Anda memegang banyak posisi sekaligus.

Untuk jurnal 5 hari, perkirakan **~6 trade total** (1,15/hari), tapi bisa saja 0 kalau bias
H4 sedang bearish, atau 15+ kalau kebetulan masuk periode ramai.

Sifat dasarnya tidak berubah: reaktif bukan prediktif, rasio menang/kalah ~1,05×, dan lima
hari terlalu pendek untuk menyimpulkan apa pun soal profitabilitas.
