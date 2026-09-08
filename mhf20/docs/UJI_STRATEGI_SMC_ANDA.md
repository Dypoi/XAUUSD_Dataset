# Backtest Strategi Anda: Trendline → OB → 3 TOP → CHOCH → FVG → BB

Periode diminta: **1 Jan 2026 – 1 Sep 2026**.

Dua istilah ambigu, jadi saya uji dua-duanya:
- **BB** → Bollinger Bands *dan* Breaker Block
- **3 TOP** → triple-top ketat (3 puncak sejajar <0,35%) *dan* longgar (3 swing high terakhir)

Semua deteksi **kausal**: fractal dikonfirmasi terlambat 3 bar, order block pakai
shift positif (bar lampau), trendline diregresi dari jendela tertutup, entry di bar
berikutnya. Tanpa ini, hasilnya palsu.

---

## Hasil Jan–Ags 2026 (yang Anda minta)

| Varian | n | WR | PF | Net | DD | t |
|---|---|---|---|---|---|---|
| ketat + Bollinger | 6 | 66,7% | 2,507 | +$72 | −0,35% | +1,01 |
| ketat + Breaker | 6 | 50,0% | 1,172 | +$12 | −0,48% | +0,17 |
| **longgar + Bollinger** | **11** | **72,7%** | **3,024** | **+$146** | −0,47% | +1,69 |
| longgar + Breaker | 10 | 70,0% | 2,525 | +$110 | −0,24% | +1,33 |

Sekilas luar biasa: **PF 3,02, win rate 72,7%** — jauh di atas MHF-20 (PF 1,166 di
periode yang sama).

**Tapi jangan senang dulu. Ini hampir pasti kebetulan.**

---

## Uji 1: Apakah bertahan di luar 2026?

| Varian | 10 tahun (n) | PF total | IS | OOS | **2026** |
|---|---|---|---|---|---|
| longgar + Bollinger | 75 | **0,792** | 0,630 | 0,907 | **3,024** |
| longgar + Breaker | 111 | **0,858** | 0,866 | 0,853 | 2,525 |
| ketat + Bollinger | 61 | **0,772** | 0,662 | 0,848 | 2,507 |

**Semua varian RUGI di 10 tahun** (PF 0,77–0,86; CAGR −0,18%).

Pola ini sangat khas: bagus di satu potongan kecil, rugi di mana-mana. 2026 adalah
**outlier**, bukan bukti. Kalau strateginya benar-benar punya edge, IS dan OOS akan
ikut positif — ini justru 0,63 dan 0,91.

## Uji 2: Seberapa mudah dapat PF 3,0 dari 11 trade secara kebetulan?

Saya ambil 11 trade **acak** dari kumpulan trade nyata, diulang 20.000 kali:

| | Peluang |
|---|---|
| Dapat PF ≥ 2,0 | **29,0%** |
| Dapat PF ≥ 2,5 | **19,7%** |
| Dapat PF ≥ 3,0 | **14,0%** |

**Satu dari tujuh percobaan menghasilkan PF ≥ 3,0 murni karena keberuntungan.**
Jadi PF 3,02 dari 11 trade sama sekali tidak istimewa — itu kebisingan statistik.

Bandingkan: MHF-20 punya t-stat +9,51 dari 4.337 trade. Strategi Anda t-stat +1,69
dari 11 trade — di bawah ambang signifikansi 2,0.

## Uji 3: Komponen mana yang sebenarnya bekerja?

Saya longgarkan bertahap untuk melihat siapa penyumbang, siapa perusak (Jan–Ags 2026):

| Kombinasi | n | WR | PF |
|---|---|---|---|
| CHOCH saja | 0 | — | — |
| + trend | 0 | — | — |
| + trend + FVG | 140 | 46,4% | **0,924** |
| + trend + FVG + OB | 14 | 57,1% | 1,512 |
| + trend + FVG + OB + BB | 11 | 72,7% | 3,024 |

Perhatikan barisan ketiga: dengan sampel layak (**140 trade**), hasilnya **PF 0,924 —
rugi**. Begitu ditambah OB dan BB, sampel anjlok ke 11 dan PF melonjak.

Itu bukan filter yang menemukan edge. Itu filter yang **memotong sampel sampai tersisa
segelintir trade yang kebetulan menang.**

---

## Kenapa ini terjadi

Setiap syarat yang Anda tumpuk memotong jumlah sinyal:

| Komponen | Frekuensi |
|---|---|
| trend_up | 50,8% bar |
| ob_touch | 35,2% bar |
| choch | 3,2% bar |
| fvg | 9,6% bar |
| bb_break | 5,2% bar |

Enam syarat dikalikan → tersisa **11 sinyal dalam 8 bulan**. Dengan sampel sekecil itu,
hasil apa pun bisa muncul.

Ini jebakan paling umum dalam desain strategi: **makin banyak konfirmasi, makin cantik
backtest-nya, makin tidak berarti hasilnya.** Enam syarat terdengar teliti, tapi
efeknya sama dengan memilih 11 trade acak.

---

## Catatan bug yang saya temukan sendiri

Versi pertama deteksi "3 TOP" saya salah: memakai `ffill` sehingga ketiga puncak
menunjuk nilai yang sama, membuat `top3_ketat` menyala di **97% bar** (harusnya jarang).
Sudah diperbaiki dengan mengambil tiga swing high yang benar-benar berbeda → turun ke
57%. Hasil di atas sudah pakai versi yang benar.

Saya sebutkan karena kalau tidak ketahuan, angkanya akan terlihat lebih meyakinkan
dan tetap salah.

---

## Perbandingan

| | Strategi Anda (terbaik) | MHF-20 standar |
|---|---|---|
| Trade 10 thn | 75 | **4.337** |
| PF 10 thn | **0,792** | **1,374** |
| CAGR | −0,18% | **9,92%** |
| t-stat | −0,91 | **+9,51** |
| PF 2026 | 3,024 | 1,166 |

---

## Kesimpulan jujur

Strategi Anda **menang di 2026 tapi rugi di sembilan tahun lainnya**, dengan sampel yang
terlalu kecil untuk menyimpulkan apa pun. Saya tidak menyarankan menjalankannya.

Tapi idenya tidak sia-sia — ada bagian yang layak diselamatkan:

1. **CHOCH + FVG + trend** menghasilkan 140 trade (sampel layak). PF-nya 0,924, jadi
   belum berhasil, tapi **inilah kerangka yang bisa dikerjakan** karena bisa diuji.
2. **Order block** menarik: menaikkan PF 0,924 → 1,512. Tapi memotong sampel 140 → 14,
   jadi belum bisa dipastikan nyata. Ini kandidat paling layak diteliti lebih lanjut.
3. **Buang "3 TOP"** — di versi longgar ia menyala 100% bar (tidak memfilter apa pun),
   di versi ketat hasilnya justru lebih buruk.

Kalau Anda mau, saya bisa uji **CHOCH + FVG + order block** secara serius di 10 tahun
penuh dengan variasi parameter, dan lihat apakah order block benar-benar punya edge atau
cuma kebetulan tadi. Itu jalur yang lebih menjanjikan daripada menumpuk enam syarat.

Kode uji: `research/smc_user.py`
