# Order Block pada MHF-20 + Setelan untuk Target Anda

Dua pertanyaan sekaligus:
1. Apakah order block menambah nilai pada sistem yang **sudah** ber-edge?
2. Setelan mana yang **bertahan 1 tahun**, **≥1 entry/hari**, dan tetap **profitable**?

---

## Bagian 1: Order Block pada MHF-20

Dasar: MHF-20 mode standar = **PF 1,304**, 2,03 entry/hari.

Sembilan variasi parameter OB ditambahkan sebagai filter:

| push | lb | n | /hari | PF | IS | OOS |
|---|---|---|---|---|---|---|
| 0.5 | 2 | 1.690 | 0,70 | 1,231 | 1,219 | 1,241 |
| 0.5 | 3 | 1.694 | 0,70 | 1,251 | 1,330 | 1,185 |
| 0.5 | 6 | 1.652 | 0,69 | 1,336 | 1,223 | 1,443 |
| 0.8 | 2 | 1.149 | 0,48 | 1,141 | 1,235 | 1,056 |
| 0.8 | 3 | 1.278 | 0,53 | 1,280 | 1,333 | 1,232 |
| **0.8** | **6** | 1.155 | 0,48 | **1,401** | 1,427 | 1,375 |
| 1.2 | 2 | 578 | 0,24 | 1,238 | 1,125 | 1,354 |
| 1.2 | 3 | 562 | 0,23 | 1,430 | 1,112 | 1,767 |
| **1.2** | **6** | 447 | 0,19 | **1,700** | 2,175 | 1,440 |

**9 dari 9 lulus IS+OOS.** Ini sangat berbeda dari uji sebelumnya (4 dari 12) — di sini
hasilnya berupa **dataran**, bukan puncak tunggal. Itu ciri efek nyata.

### Uji plasebo

OB (push 0.8, lb 6) menyisakan 14% sinyal. Diganti filter **acak** berfrekuensi sama, 30×:

| | PF |
|---|---|
| 30 filter acak (rata-rata) | 1,264 |
| Filter acak terbaik | 1,430 |
| **Order block** | **1,401** |
| Peluang acak ≥ 1,401 | **3,3% (1 dari 30)** |

Order block mengalahkan 29 dari 30 plasebo.

### Kesimpulan bagian 1

**Order block memang menambah nilai** pada MHF-20: PF 1,304 → 1,401, dan konsisten di
seluruh 9 variasi parameter. Ini bukti jauh lebih kuat daripada uji sebelumnya.

**Tapi ada harga yang mahal** — lihat bagian 2.

---

## Bagian 2: Syarat Anda — bertahan 1 tahun, ≥1 entry/hari

Saya uji **108 jendela 12-bulan bergulir** (mulai tiap bulan, 2016–2026). Ini uji yang
tepat untuk "bertahan 1 tahun": bukan satu tahun keberuntungan, tapi *semua* tahun.

| Setelan | /hari | PF | **Tahun profit** | Tahun terburuk |
|---|---|---|---|---|
| **Tanpa OB, dist 1.5** | **1,79** | 1,374 | **91,7%** | −$501 |
| Tanpa OB, dist 0.5 | 2,03 | 1,280 | 86,1% | −$827 |
| Mode aktif (cap 5) | 1,15 | 1,353 | 91,7% | −$692 |
| +OB 0.5/6 | 0,69 | 1,318 | **62,0%** | −$726 |
| +OB 0.8/6 | 0,48 | 1,313 | **66,7%** | −$550 |

**Inilah temuan pentingnya.** Order block menaikkan PF, tapi **menurunkan keandalan
tahunan dari 91,7% menjadi 62%.**

Penyebabnya: OB memangkas sinyal hingga tersisa 14–34%, jadi hanya ~120–172 trade per
tahun. Dengan sampel sekecil itu dalam satu tahun, hasilnya jadi undian — PF jangka
panjang bagus, tapi tahun individual sering merah.

**OB juga gagal memenuhi syarat Anda**: maksimum 0,70 entry/hari, jauh di bawah 1/hari.

Jadi ada pertukaran langsung:
- **Mau PF tertinggi?** Pakai OB → tapi 1 dari 3 tahun rugi, dan entry jarang.
- **Mau bertahan tiap tahun + entry sering?** Jangan pakai OB.

Target Anda jelas menuntut yang kedua.

---

## Setelan baru: MODE HARIAN (sudah aktif)

```python
MODE                = "harian"
MAX_ENTRIES_PER_DAY = 0        # tanpa cap
RISK_PER_POSITION   = 20.0
MAX_CONCURRENT      = 8        # risiko maks terbuka $160 (1,6%)
BIAS_MIN_DIST_PCT   = 1.50
MAX_ORDERS_PER_DAY  = 12       # rem keras
```

### Hasil

| Metrik | Nilai |
|---|---|
| Trades | 4.337 |
| **Entry/hari** | **1,79** ✓ |
| Win rate | **56,63%** |
| Profit Factor | **1,374** |
| Equity | $10.000 → $24.792 |
| CAGR | **9,92%** |
| Max Drawdown | **−9,31%** |
| Ekspektasi | +0,171R |
| t-stat | **+9,51** |

### Syarat "bertahan 1 tahun"

| | |
|---|---|
| Jendela 12-bulan diuji | 108 |
| **Profit** | **91,7%** (99 dari 108) |
| PF median tahunan | 1,346 |
| Tahun terburuk | **−$501** (−5,0% akun) |
| Tahun terbaik | +$5.040 |

**Ini yang terbaik dari semua mode**, sekaligus DD terendah (−9,31%) dan t-stat tertinggi
(+9,51).

---

## Jawaban jujur atas target Anda

| Syarat Anda | Status |
|---|---|
| Bertahan 1 tahun | **91,7% jendela profit** ✓ |
| Minimal 1 entry/hari | **1,79/hari rata-rata** ✓ |
| Tetap profitable | **PF 1,374, CAGR 9,92%** ✓ |

Ketiganya terpenuhi. Tapi dua catatan yang harus Anda pegang:

**1. "1,79 entry/hari" tetap rata-rata, bukan jaminan harian.**
Hanya **22% hari** yang ada entry (674 dari 3.110). Sisanya kosong — sinyalnya
menggerombol. Anda tetap akan mengalami minggu-minggu sepi. Tidak ada setelan yang bisa
menghilangkan ini tanpa merusak edge; sudah saya buktikan waktu menguji pembuangan
syarat entry.

**2. 8,3% jendela tahunan RUGI.** Sembilan dari 108 tahun merah, terburuk −$501 (−5%
akun). Kalau Anda kebetulan mulai di jendela itu, setahun penuh bisa berakhir minus.
Itu bukan kerusakan — itu bagian normal dari edge tipis.

---

## Soal order block

Saya **tidak** memasukkannya ke default, meski PF-nya lebih tinggi. Alasannya murni
karena target Anda: OB memberi 0,48–0,70 entry/hari (gagal syarat) dan keandalan tahunan
hanya 62–67% (gagal syarat utama Anda).

Tapi temuannya nyata dan saya simpan: **9 dari 9 variasi lulus IS+OOS, mengalahkan 29
dari 30 plasebo.** Kalau suatu saat Anda lebih mementingkan kualitas per-trade daripada
frekuensi dan konsistensi tahunan, OB 0.8/6 adalah kandidat serius.

**Audit: paritas 191/191 · resilience 85/85 · eksekusi 38/38.**

Satu tes eksekusi sempat gagal karena `MAX_ENTRIES_PER_DAY=0` membuat skenario cap tidak
berlaku; sudah diperbaiki agar mode tanpa-cap tetap diuji (memastikan cap **tidak**
memblokir entry normal, sementara rem keras tetap bekerja).
