# Dari Mana Profit MHF-20 Sebenarnya Datang?

Pertanyaan: **menangkap pisau jatuh, atau ikut pisau terbang?**

Jawaban singkat: **pisau terbang** — dan bahkan lebih ekstrem dari itu.

---

## 1. MHF-20 hampir tidak pernah menangkap pisau

Momentum harga tepat sebelum entry (6.274 trade):

| Jendela sebelum entry | Harga sedang NAIK | Median gerakan |
|---|---|---|
| 1 jam | **91,4%** | +20,9 bps |
| 4 jam | **94,3%** | +45,5 bps |
| 24 jam | **92,2%** | +81,1 bps |

Posisi entry relatif range 24 jam:

| | |
|---|---|
| Median posisi | **96,7% dari bawah range** |
| Entry di paruh atas range | 98,3% |
| Entry di 20% teratas | 85,6% |
| **Entry di 20% terbawah** | **0,0%** |

**Nol persen.** Sistem ini secara struktural **tidak bisa** menangkap pisau jatuh —
syarat *sweep BSL* menuntut harga sudah menembus high sesi, jadi entry selalu terjadi
di puncak range, setelah kenaikan.

## 2. Dan memang di situlah uangnya

| Kondisi entry | n | % | PF | Net |
|---|---|---|---|---|
| Harga TURUN 1 jam sebelumnya (nangkap pisau) | 539 | 8,6% | 1,066 | +$362 |
| **Harga NAIK 1 jam sebelumnya (ikut momentum)** | **5.735** | **91,4%** | **1,228** | **+$12.205** |

Yang 8,6% "nangkap pisau" itu praktis impas (PF 1,066 — nyaris tidak ada edge).
**97% profit datang dari mengikuti momentum.**

---

## 3. Tapi ini bukan "ikut tren lalu untung besar"

Justru sebaliknya. Anatomi kemenangannya rapuh:

| | Menang | Kalah |
|---|---|---|
| Jumlah | 3.369 (53,7%) | 2.905 (46,3%) |
| Rata-rata | **+$21,27** | **−$20,34** |
| Total | +$71.652 | −$59.085 |

**Rasio menang/kalah cuma 1,05×.** Menang dan kalah hampir sama besarnya. Sistem ini
tidak menang karena "profit besar, rugi kecil" — ia menang karena **sedikit lebih sering
benar** (53,7% vs 46,3%).

Dari $71.652 kotor, $59.085 langsung habis untuk menutup kerugian. Sisanya **$12.567**
adalah seluruh keuntungan 10 tahun. Marginnya **17,5%** dari perputaran kotor.

### Dari mana kontribusinya

| Exit | n | Total | Kontribusi |
|---|---|---|---|
| TP2 (target 2R) | 1.115 | +$40.140 | +319% |
| TIME (stop 24 jam) | 1.972 | +$14.632 | +116% |
| BE (break-even+) | 941 | +$11.789 | +94% |
| **SL** | **2.246** | **−$53.994** | **−430%** |

Pembacaannya: **TP2 adalah satu-satunya mesin profit sejati.** Hanya 17,8% trade mencapai
target penuh, tapi menyumbang $40.140. Sisanya adalah manajemen kerugian — BE menyelamatkan
941 trade dari jadi rugi, TIME menutup posisi mengambang dengan untung tipis.

**Tanpa mekanisme BE dan time-stop, sistem ini rugi.** SL sendirian menghapus 4,3× dari
net profit.

---

## 4. Jadi metafora yang tepat apa?

Bukan menangkap pisau. Bukan juga menunggangi tren besar.

**MHF-20 itu seperti kasino yang mengambil taruhan koin dengan peluang 53,7%.**

- Ia tidak meramal apa pun (lihat `HONEST_LIMITS.md`: edge arah cuma +0,47 pp)
- Ia tidak menunggu setup sempurna — ia masuk 2,54× per hari
- Setiap taruhan hampir seimbang (menang $21,27 vs kalah $20,34)
- Keuntungan hanya muncul setelah **ribuan** pengulangan

Kalau harus memakai istilah pisau: sistem ini **menempel di belakang pisau yang sedang
terbang naik, memegangnya rata-rata 6–15 jam, lalu melepas** — kadang di target (TP2),
lebih sering di titik impas (BE) atau saat waktu habis (TIME).

---

## 5. Kelemahan yang mengikuti dari struktur ini

Karena profitnya bergantung pada momentum lanjutan, MHF-20 rentan pada:

1. **Pasar sideways/choppy** — sweep BSL terjadi, tapi harga langsung balik. Ini yang
   menghasilkan 2.246 trade SL.
2. **Bear market panjang** — filter H4 mematikan sistem, tapi filter itu terlambat
   ~11 hari, jadi ada periode entry beruntun yang salah.
3. **Sampel bullish** — 2016–2026 emas naik +230%. Sistem long-only belum pernah diuji
   pada bear market gold yang panjang.
4. **Margin tipis** — 17,5% dari perputaran kotor. Biaya naik sedikit saja (spread,
   swap, slippage) langsung menggerus. Stress test +5 pips menurunkan PF 1,203 → 1,046.

Poin 4 inilah alasan **swap** jadi risiko terbesar yang belum dimodelkan: Exness
mengiklankan −$0,53/lot/malam untuk long. Dengan median holding 15,1 jam dan 8 posisi
paralel, biaya itu menyerang tepat di margin yang cuma 17,5%.
