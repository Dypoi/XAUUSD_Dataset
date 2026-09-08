# Pembuktian 3 Ide: Buang 3TOP · Inti CHOCH+FVG+Trend · Order Block

Diuji **10 tahun penuh** (2016–2026), bukan 8 bulan. Ini bedanya bukti dan kebetulan.

---

## Ide 1: Buang "3 TOP" — **TERBUKTI, tapi karena alasan lain**

| Kombinasi | n | PF | IS | OOS |
|---|---|---|---|---|
| **Inti (CHOCH+FVG+trend)** | 1.586 | 0,998 | 0,930 | 1,054 |
| + 3TOP longgar | **1.586** | **0,998** | 0,930 | 1,054 |
| + 3TOP ketat | 1.221 | 1,004 | 0,929 | 1,069 |

Versi longgar menghasilkan angka **persis identik** — ia tidak memfilter apa pun sama
sekali. Versi ketat memangkas 23% sinyal dan hanya mengubah PF 0,998 → 1,004 (tidak berarti).

**Kesimpulan: buang saja.** Terbukti tidak berkontribusi.

---

## Ide 2: Inti CHOCH+FVG+trend — **SAMPEL LAYAK, TAPI TANPA EDGE**

| | Nilai |
|---|---|
| n | **1.586** (sampel sangat layak) |
| PF | **0,998** |
| CAGR | −0,03% |
| t-stat | −0,03 |
| IS / OOS | 0,930 / 1,054 |

PF 0,998 artinya **persis impas** — setiap $1 rugi diimbangi $0,998 untung. Sebelum biaya
tambahan, ini nol. Setelah swap, ini rugi.

Dugaan saya di jawaban sebelumnya (PF 0,924 dari 140 trade di 2026) ternyata tidak
melenceng: pada 1.586 trade angkanya 0,998. Sampelnya kini kuat, dan kesimpulannya jelas —
**kerangka ini tidak punya edge sendiri.**

Nilainya bukan sebagai strategi, tapi sebagai **fondasi yang bisa diuji** karena sampelnya
besar.

---

## Ide 3: Order Block — **INI CERITA YANG RUMIT**

Parameter awal saya ternyata kebetulan yang buruk:

| Kombinasi | n | PF | IS | OOS |
|---|---|---|---|---|
| inti + OB (push 0.8, lb 2) | 133 | **0,691** | 0,696 | 0,687 |

Jadi saya uji **12 variasi parameter** secara sistematis:

| push | lookback | n | PF | IS | OOS | t |
|---|---|---|---|---|---|---|
| 0.5 | 2 | 129 | 0,983 | 0,660 | 1,216 | −0,09 |
| 0.5 | 3 | 240 | 1,130 | 1,487 | 0,973 | +0,87 |
| **0.5** | **6** | **322** | **1,205** | 1,351 | 1,111 | +1,53 ✓ |
| 0.8 | 2 | 133 | 0,691 | 0,696 | 0,687 | −1,96 |
| **0.8** | **3** | **216** | **1,206** | 1,320 | 1,130 | +1,26 ✓ |
| **0.8** | **6** | **270** | **1,145** | 1,199 | 1,104 | +1,01 ✓ |
| 1.2 | 2 | 101 | 0,900 | 1,342 | 0,654 | −0,48 |
| **1.2** | **3** | **141** | **1,448** | **1,482** | **1,416** | **+1,96** ✓ |
| 1.2 | 6 | 164 | 0,943 | 0,877 | 0,998 | −0,34 |

**4 dari 12 variasi lulus** (PF>1,05 dengan IS dan OOS sama-sama >1,0).

### Kandidat terbaik: push 1.2, lookback 3

Uji tambahan pada kandidat ini:

**A. Tahan biaya** — ya:

| Slippage | PF |
|---|---|
| +$0,00 | 1,448 |
| +$0,20 | 1,341 |
| +$0,50 | **1,248** |

**B. Konsistensi tahunan** — 8 dari 11 tahun positif:

| Tahun | n | PF | Tahun | n | PF |
|---|---|---|---|---|---|
| 2016 | 5 | 0,182 | 2022 | 13 | 1,169 |
| 2017 | 11 | 2,235 | 2023 | 8 | **0,188** |
| 2018 | 7 | **0,104** | 2024 | 21 | 3,745 |
| 2019 | 9 | 2,935 | 2025 | 27 | 0,983 |
| 2020 | 14 | 2,770 | 2026 | 9 | 2,025 |
| 2021 | 17 | 2,482 | | | |

**C. Uji plasebo** — OB diganti filter **acak** berfrekuensi sama, 30 kali:

| | PF |
|---|---|
| 30 filter acak (rata-rata) | 1,024 |
| Filter acak terbaik | 1,379 |
| **Order block asli** | **1,448** |
| Peluang acak ≥ 1,448 | **0 dari 30** |

Order block mengalahkan seluruh 30 filter acak. Ini poin terkuatnya.

---

## Tapi ini uji yang menjatuhkannya

Saya mencoba **12 kombinasi parameter lalu memilih yang terbaik.** Itu wajib
dikoreksi — kalau mencoba cukup banyak, sesuatu pasti terlihat bagus.

Distribusi null (data tanpa edge, n=141):

| | Peluang |
|---|---|
| SATU percobaan capai PF ≥ 1,448 | **2,63%** |
| **TERBAIK dari 12 percobaan** | **27,37%** |

**Lebih dari seperempat.** Kalau saya menguji 12 parameter pada data yang sama sekali
tidak punya edge, peluang menemukan "PF 1,448" adalah 27%.

Jadi meski uji plasebo terlihat meyakinkan, **setelah dikoreksi jumlah percobaan, hasilnya
tidak signifikan.**

---

## Kesimpulan jujur

| Ide | Vonis |
|---|---|
| **1. Buang 3 TOP** | **Terbukti benar** — tidak memfilter apa pun |
| **2. Inti CHOCH+FVG+trend** | **Sampel layak (1.586), tapi PF 0,998 = tanpa edge** |
| **3. Order block** | **Menjanjikan tapi BELUM TERBUKTI** |

Order block bukan omong kosong — 4 dari 12 variasi lulus IS+OOS, ia mengalahkan 30 filter
acak, dan tahan biaya. Itu lebih dari yang bisa dikatakan kebanyakan ide.

Tapi tiga hal menahan saya menyebutnya terbukti:

1. **n=141 dalam 10 tahun** = ~14 trade/tahun. Terlalu jarang untuk dipercaya.
2. **Sensitif parameter** — push 1.2/lb 3 memberi PF 1,448; push 0.8/lb 2 memberi 0,691.
   Edge nyata biasanya berupa dataran, bukan satu titik (bandingkan filter tren MHF-20:
   **25 dari 25** kombinasi mengungguli baseline).
3. **Koreksi multiple-testing: 27%.** Ini yang paling menentukan.

**Saya tidak menyarankan menjalankannya**, dan saya tidak mengubah default apa pun.

---

## Yang akan saya lakukan berikutnya kalau Anda mau

Order block layak diteliti lebih jauh, tapi dengan cara yang benar:

1. **Longgarkan inti** agar sampel OB naik dari 141 ke ~500+. Tanpa sampel, tidak akan
   pernah bisa dibuktikan.
2. **Uji OB pada MHF-20** — apakah menambah nilai di atas sistem yang sudah ber-edge?
   Ini uji yang lebih adil daripada menumpuknya pada inti yang PF-nya 0,998.
3. **Cari dataran parameter**, bukan puncak. Kalau push 0.5–1.5 dan lb 2–8 semuanya
   >1,1, itu baru meyakinkan.

Poin 2 yang paling menarik menurut saya: kalau order block benar-benar menandai zona
institusional, ia harusnya memperbaiki sistem yang sudah bekerja — bukan cuma
menyelamatkan kerangka yang impas.

Kode: `research/smc_user.py`
