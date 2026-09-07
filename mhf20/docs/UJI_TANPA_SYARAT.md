# Bagaimana Kalau Sweep BSL dan Break Swing/FVG Ditiadakan?

Anda melihat "TIDAK ENTRY · Terhalang: Sweep BSL; Candle bullish; Break swing/FVG" dan
bertanya apa jadinya kalau syarat itu dibuang. Sudah saya backtest keempat kombinasinya.

**Jawaban singkat: jangan dibuang.** Sekilas hasilnya terlihat lebih baik, tapi itu ilusi.

---

## 1. Hasil mentah (mode aktif, cap 5/hari, risiko $40)

| Varian | n | /hari | WR | PF | Equity | CAGR | MaxDD |
|---|---|---|---|---|---|---|---|
| **SEKARANG (semua syarat)** | 2.779 | 1,15 | **55,70%** | **1,353** | $23.061 | 9,10% | −11,83% |
| Tanpa Sweep BSL | 5.738 | 2,37 | 53,78% | 1,247 | **$29.721** | **12,00%** | −11,52% |
| Tanpa Break swing/FVG | 4.699 | 1,94 | 53,37% | 1,263 | $27.497 | 11,11% | −15,15% |
| Tanpa keduanya | 6.158 | 2,54 | 52,97% | 1,216 | $29.040 | 11,73% | −13,57% |

Terlihat menggoda: buang Sweep BSL, CAGR naik 9,10% → 12,00%.

**Tapi perhatikan PF turun di semua varian.** Equity naik bukan karena kualitasnya lebih
baik — melainkan karena **jumlah trade 2× lipat**. Anda mengambil risiko dua kali lebih
sering untuk edge per-trade yang lebih buruk.

## 2. Perbandingan adil: samakan risikonya

Kalau risiko disetel agar drawdown-nya setara (~−11,8%):

| Varian | risk | n | PF | Equity | CAGR | Ekspektasi |
|---|---|---|---|---|---|---|
| **SEKARANG** | $40 | 2.779 | **1,353** | $23.061 | 9,10% | **+0,117R** |
| Tanpa Sweep | $40 | 5.738 | 1,247 | **$29.721** | **12,00%** | +0,086R |
| Tanpa Break/FVG | $20 | 4.700 | 1,264 | $21.724 | 8,42% | +0,125R |
| Tanpa keduanya | $20 | 6.159 | 1,216 | $22.720 | 8,91% | +0,103R |

Dua varian justru lebih buruk dari sistem sekarang. Hanya "tanpa Sweep" yang unggul —
tapi lihat poin berikutnya.

## 3. Ketahanan biaya — di sinilah semuanya runtuh

Ingat: **swap belum dimodelkan** dan margin sistem ini tipis.

| Varian | +$0,00 | +$0,10 | +$0,20 | +$0,50 |
|---|---|---|---|---|
| **SEKARANG** | 1,353 | 1,321 | **1,290** | **1,171** |
| Tanpa Sweep | 1,247 | 1,213 | 1,178 | **0,991** ← rugi |
| Tanpa Break/FVG | 1,263 | 1,236 | **0,888** ← rugi | 0,759 |
| Tanpa keduanya | 1,216 | 1,185 | 1,158 | **0,992** ← rugi |

**Ketiga varian tanpa syarat berubah RUGI pada biaya realistis.** Sistem sekarang masih
PF 1,171 di +$0,50/sisi.

"Tanpa Break/FVG" bahkan kolaps di +$0,20 — biaya yang sangat mungkin Anda temui.

Keunggulan CAGR 12% itu **hanya ada di dunia tanpa biaya tambahan**. Begitu spread melebar
atau swap masuk hitungan, keunggulannya hilang.

## 4. IS / OOS

| Varian | IS | OOS | 2026 |
|---|---|---|---|
| **SEKARANG** | **1,382** | 1,330 | 0,961 |
| Tanpa Sweep | 1,164 | 1,325 | 1,085 |
| Tanpa Break/FVG | 1,164 | 1,354 | **0,808** |
| Tanpa keduanya | 1,133 | 1,290 | 1,009 |

Sistem sekarang satu-satunya yang **konsisten kuat di kedua periode**. Varian lain
IS-nya lemah (1,13–1,16) — artinya edge-nya bergantung pada periode tertentu.

## 5. Yang paling menentukan: apakah masih strategi?

Berapa persen bar yang lolos jadi sinyal?

| Varian | Bar lolos | % dari semua bar |
|---|---|---|
| **SEKARANG** | 7.586 | **1,07%** |
| Tanpa Sweep | 41.716 | 5,89% |
| Tanpa Break/FVG | 47.878 | 6,75% |
| **Tanpa keduanya** | 267.896 | **37,79%** |

Tanpa kedua syarat, sistem masuk di **hampir 38% dari semua bar** — praktis "beli kapan
saja selama tren bullish". Itu bukan strategi entry, itu beli-tahan dengan langkah kecil.

### Uji kontrol: entry acak

Saya jalankan entry **acak** dengan frekuensi sama, hanya saat bias bullish:

| | PF |
|---|---|
| Acak (rata-rata 5 seed) | **1,138** |
| Tanpa keduanya | 1,216 |
| Tanpa Sweep | 1,247 |
| **SEKARANG** | **1,353** |

Sistem sekarang unggul **+0,215 di atas entry acak**. Varian "tanpa keduanya" cuma
unggul +0,078 — sebagian besar hasilnya datang dari filter tren dan manajemen posisi,
bukan dari keputusan entry.

Dengan kata lain: **membuang kedua syarat membuang hampir seluruh nilai entry-nya.**

---

## Kesimpulan

| Pertanyaan | Jawaban |
|---|---|
| Bisa lebih sering entry? | Ya, 1,15 → 2,54/hari |
| Untung lebih besar? | Hanya di atas kertas, tanpa biaya tambahan |
| Kualitas per trade? | **Turun** (PF 1,353 → 1,216; WR 55,7% → 53,0%) |
| Tahan biaya nyata? | **Tidak** — rugi di +$0,20…+$0,50 |
| Masih punya edge entry? | **Nyaris tidak** — cuma +0,078 di atas acak |

**Rekomendasi saya: pertahankan kedua syarat.** Saya tidak mengubah default.

Ini konsisten dengan temuan lama yang sudah tercatat di `HONEST_LIMITS.md`: melonggarkan
filter entry untuk menaikkan frekuensi selalu menghancurkan edge. Sudah terbukti pada
pullback-to-MA, RSI oversold, N-bar breakout, dan displacement mentah — sekarang
terkonfirmasi lagi.

---

## Kalau Anda tetap ingin lebih sering entry

Ada cara yang **tidak** merusak kualitas — longgarkan filter tren, bukan syarat entry:

| Setelan | n | /hari | PF | CAGR | DD |
|---|---|---|---|---|---|
| `BIAS_MIN_DIST_PCT = 1.50` (sekarang) | 2.779 | 1,15 | 1,353 | 9,10% | −11,83% |
| `BIAS_MIN_DIST_PCT = 0.50` | 3.157 | 1,31 | 1,280 | 6,33% | −9,86% |
| `MAX_ENTRIES_PER_DAY = 0` + dist 0.50 | 4.905 | 2,03 | 1,304 | 9,50% | −11,68% |

Opsi terakhir (mode standar) memberi **2,03 entry/hari dengan PF 1,304** — jauh lebih baik
daripada 2,54/hari dengan PF 1,216 hasil membuang syarat entry.

Kalau mau lebih ramai, bilang saja dan saya pindahkan ke mode standar.

---

## Catatan soal layar "TIDAK ENTRY"

Yang Anda lihat itu **normal**. 75% hari memang tanpa sinyal, dan hanya 1,07% bar yang
lolos. Panel itu menampilkan syarat yang belum terpenuhi **setiap detik** — jadi hampir
sepanjang waktu akan terlihat merah.

Yang perlu dikhawatirkan bukan "sering merah", tapi kalau **berminggu-minggu tidak ada
entry sama sekali padahal tren bullish** — itu baru tanda ada yang rusak.
