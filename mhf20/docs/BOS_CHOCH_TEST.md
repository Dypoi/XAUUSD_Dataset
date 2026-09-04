# Apakah MHF-20 perlu BOS / CHoCH?

**Jawaban: TIDAK.** Diuji langsung, semua varian memperburuk sistem kecuali satu yang efeknya nol.

## Cara uji

Struktur swing dibangun **kausal** dengan fractal k=5: sebuah swing high di bar `j` baru
dianggap "diketahui" pada bar `j+5`. Tanpa penundaan ini, filter BOS bocor ke masa depan
dan hasilnya palsu (kelas bug yang sama dengan Order Block di R3 dan `sessions.py` di bot ICAS).

Tiga filter diuji sebagai syarat TAMBAHAN di atas sinyal MHF-20:
- **BOS naik** — close > swing high terkonfirmasi terakhir
- **HH & HL** — swing high naik DAN swing low naik (uptrend struktural penuh)
- **Larang CHoCH turun** — tolak entry bila close < swing low terakhir

## Hasil

| Varian | n | /hari | WR% | PF | Equity | DD% | exp R | t |
|---|---|---|---|---|---|---|---|---|
| **MHF-20 baseline** | **6.274** | **2,54** | **53,70** | **1,213** | **$22.567** | **−14,47** | **+0,100** | **6,89** |
| + filter BOS naik | 5.234 | 2,12 | 52,87 | 1,171 | $18.574 | −18,17 | +0,082 | 5,15 |
| + filter HH&HL | 3.954 | 1,60 | 52,96 | 1,181 | $16.730 | −17,18 | +0,085 | 4,71 |
| + larang CHoCH turun | 6.264 | 2,53 | 53,75 | 1,215 | $22.677 | −14,44 | +0,101 | 6,96 |
| + BOS & HH&HL | 2.860 | 1,16 | 51,75 | 1,112 | $13.119 | −18,63 | +0,055 | 2,55 |

**Setiap filter struktur menurunkan PF, menaikkan drawdown, dan memangkas frekuensi.**
Kombinasi terketat (BOS & HH&HL) adalah yang terburuk: equity turun dari $22.567 ke $13.119.

Larangan CHoCH turun hanya menolak 44 dari 11.374 sinyal (0,4%) — perubahannya (+0,002 PF)
adalah derau, bukan perbaikan.

## Uji pembeda: apakah BOS punya daya diskriminasi sama sekali?

Kalau BOS informatif, subset "sudah BOS" harus jelas mengungguli subset "belum BOS".

| Subset | n | WR% | PF | exp R | t |
|---|---|---|---|---|---|
| Sudah BOS naik | 5.234 | 52,87 | **1,171** | +0,082 | 5,15 |
| Belum BOS | 3.518 | 53,10 | **1,163** | +0,075 | 3,99 |
| Uptrend HH&HL | 3.954 | 52,96 | **1,181** | +0,085 | 4,71 |
| Bukan uptrend HH&HL | 4.366 | 53,44 | **1,188** | +0,088 | 5,09 |

Selisih PF **0,008** dan **0,007** — nol secara praktis. Untuk HH&HL arahnya bahkan terbalik:
trade yang BUKAN dalam uptrend struktural justru sedikit lebih baik.

**BOS/CHoCH tidak memisahkan trade bagus dari trade jelek pada sistem ini.**

## Mengapa begitu

MHF-20 **sudah** mengandung informasi struktur, dua kali:
1. **Sweep BSL** — syarat entry sudah menuntut harga menembus likuiditas sesi. Itu BOS
   mini yang sudah terjadi. Menambah filter BOS = menyaring dua kali hal yang sama.
2. **Bias H4-MA240** — sudah menjadi proksi tren jangka menengah, dan sudah terlambat
   ~11 hari. Menumpuk HH&HL di atasnya menambah keterlambatan kedua.

Filter struktur di sini bukan menambah informasi, melainkan **memotong ukuran sampel**.
Edge MHF-20 hanya +0,47 pp per trade; edge sekecil itu butuh n besar untuk terwujud.
Memangkas 6.274 → 2.860 trade menghancurkan justru mekanisme yang membuat sistem ini bekerja.

## Kesimpulan

Jangan tambahkan BOS/CHoCH. Untuk sistem yang edge-nya tipis dan bergantung pada repetisi,
setiap filter tambahan harus membayar ongkosnya dalam bentuk kenaikan expectancy yang lebih
besar daripada kerugian akibat n yang mengecil. BOS/CHoCH gagal memenuhi syarat itu —
ia bahkan tidak punya daya pisah sama sekali (ΔPF 0,008).
