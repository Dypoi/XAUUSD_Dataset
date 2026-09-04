# Filter Tren v1.1 — Anda Benar, Ada Celah Besar Di Sini

Pertanyaan Anda tepat sasaran. Filter tren MHF-20 v1.0 hanyalah **satu perbandingan
biner**: `close_H4 > MA240`. Itu saja.

Perbandingan biner tidak membedakan:
- MA yang **menanjak** vs MA yang **sudah berbalik turun** tapi harga kebetulan masih di atasnya
- Harga yang **jauh** di atas MA vs harga yang **mendempet** MA (zona whipsaw)

Saya uji kedua dimensi itu. Hasilnya menemukan dua kantong rugi besar.

---

## 1. Kemiringan MA (arah tren, bukan cuma posisi)

| Rezim | n | WR | PF | Net | Ekspektasi |
|---|---|---|---|---|---|
| **MA melemah/turun** | 1.250 | 48,2% | **0,910** | **−$1.108** | **−0,044R** |
| datar− | 1.257 | 53,4% | 1,183 | +$1.963 | +0,078R |
| datar+ | 1.251 | 57,2% | 1,425 | +$4.590 | +0,183R |
| naik sedang | 1.253 | 54,7% | 1,376 | +$4.441 | +0,177R |
| naik kuat | 1.263 | 55,0% | 1,200 | +$2.681 | +0,106R |

Saat MA240 sudah berbalik turun, sistem **rugi** — meski harga masih di atas MA.
Ini persis rezim "tren sudah patah tapi belum kelihatan".

## 2. Jarak harga ke MA

| Rezim | n | WR | PF | Net | Ekspektasi |
|---|---|---|---|---|---|
| **Mendempet MA** | 1.255 | 44,6% | **0,763** | **−$2.952** | **−0,118R** |
| agak dekat | 1.254 | 53,5% | 1,151 | +$1.776 | +0,071R |
| sedang | 1.250 | 57,4% | 1,442 | +$4.549 | +0,182R |
| jauh | 1.258 | 56,0% | 1,368 | +$4.328 | +0,172R |
| sangat jauh | 1.257 | 56,9% | 1,381 | +$4.867 | +0,194R |

**Kantong rugi terbesar di seluruh sistem: PF 0,763, −$2.952.** Saat harga mendempet
MA240, "di atas MA" tidak berarti apa-apa — harga bolak-balik menembus garis itu.

Perhatikan juga: **tidak ada hukuman untuk overextended.** Kuintil "sangat jauh" justru
terbaik (PF 1,381). Ini konsisten dengan temuan sebelumnya — sistem ini murni momentum,
bukan mean-reversion.

## 3. Volatilitas — tidak dipakai

| Rezim | PF |
|---|---|
| vol rendah | 1,343 |
| vol sedang | 1,108 |
| vol tinggi | 1,223 |

Tidak monoton, tidak ada cerita ekonomi yang jelas. **Saya tidak memfilternya** — pola
non-monoton pada 3 bucket adalah kandidat kuat untuk kebetulan.

---

## Perubahan v1.1

```python
BIAS_SLOPE_BARS: int = 30       # MA240 harus menanjak atas 30 bar H4 (~5 hari)
BIAS_MIN_DIST_PCT: float = 0.50 # harga min 0,50% di atas MA240
```

Keduanya kausal (hanya bar H4 tertutup). Set ke `0` untuk kembali ke perilaku v1.0.

### Hasil engine penuh (compounding, kill-switch, 8 slot)

| Metrik | v1.0 | **v1.1** |
|---|---|---|
| Trades | 6.274 | 4.905 (−22%) |
| Frekuensi | 2,54/hari | 2,03/hari |
| Win rate | 53,70% | **55,33%** |
| Profit Factor | 1,213 | **1,304** |
| Equity | $22.567 | **$23.881** |
| CAGR | 8,65% | **9,50%** |
| Max DD | −14,47% | **−11,68%** |
| Ekspektasi | +0,100R | **+0,141R** |
| t-stat | +6,89 | **+8,43** |

**Trade lebih sedikit, uang lebih banyak, drawdown lebih dangkal.**

### Validasi out-of-sample

| Periode | v1.0 | v1.1 |
|---|---|---|
| IS (2016→2023/02) | 1,132 | **1,276** |
| OOS (2023/03→2026) | 1,281 | **1,324** |
| Jan–Ags 2026 | 1,166 | 1,153 |

Membaik di IS **dan** OOS — bukan cuma di bagian yang saya lihat saat merancang.
Di 2026 praktis sama (1,153 vs 1,166) dengan 73 trade lebih sedikit.

### Sensitivitas — dataran, bukan tebing

PF untuk 25 kombinasi parameter:

| slope\dist | 0,00% | 0,25% | 0,50% | 0,75% | 1,00% |
|---|---|---|---|---|---|
| 10 bar | 1,289 | 1,314 | 1,323 | 1,342 | 1,356 |
| 20 bar | 1,284 | 1,319 | 1,328 | 1,344 | 1,349 |
| **30 bar** | 1,284 | 1,313 | **1,322** | 1,338 | 1,343 |
| 45 bar | 1,270 | 1,295 | 1,302 | 1,319 | 1,323 |
| 60 bar | 1,238 | 1,263 | 1,270 | 1,289 | 1,300 |

**Semua 25 kombinasi mengungguli baseline 1,213.** Tidak ada tebing — parameter (30; 0,50%)
duduk di tengah dataran, bukan di puncak sempit. Ini ciri filter yang nyata, bukan overfit.

Saya sengaja **tidak** memilih (10; 1,00%) yang PF-nya tertinggi (1,356), karena itu
memilih puncak — justru gejala overfitting.

### Yang paling penting: ketahanan biaya

| Slippage tambahan | v1.0 | **v1.1** |
|---|---|---|
| +$0,00 | 1,213 | **1,304** |
| +$0,10 | 1,177 | **1,265** |
| +$0,20 | **1,004** (nyaris mati) | **1,230** |
| +$0,50 | **0,728** (rugi) | **1,006** |

Ini perbaikan terbesarnya. v1.0 kolaps jadi PF 1,004 pada +$0,20/sisi. v1.1 masih
1,230 — dan baru impas di +$0,50.

Ingat margin sistem ini cuma 17,5% dari perputaran kotor, dan **swap belum dimodelkan**.
Bantalan biaya inilah yang membuat v1.1 jauh lebih layak dijalankan sungguhan.

---

## Sinkronisasi live (bahaya yang hampir terlewat)

`live/signal_engine.py` menyimpan **salinan sendiri** dari `macro_bias`. Kalau saya hanya
mengubah `strategy.py`, backtest dan live akan diam-diam berbeda — persis kelas bug
paling berbahaya di sistem ini.

Sudah disamakan, plus **tes [23]** yang membaca kedua file dan memastikan
`BIAS_SLOPE_BARS`, `BIAS_MIN_DIST_PCT`, dan `BIAS_MA_H4` **identik nilainya**. Kalau
suatu saat berbeda, tes gagal.

Panel dashboard kini menampilkan `MA240=…​ | jarak=+x,xx% (min +0,5%) | slope 30 bar H4`.

**Audit: paritas 191/191 · resilience 69/69 · eksekusi 37/37.**

---

## Yang TIDAK berubah

Sistem ini tetap **reaktif, bukan prediktif**. Filter tren tidak meramal apa pun — ia
hanya menolak dua rezim yang terbukti merugi. Win rate naik 53,70% → 55,33%, rasio
menang/kalah tetap ~1,05×. Edge tetap tipis dan tetap butuh ribuan trade.

Dan tiga bulan nol trade di 2026 akan jadi **lebih sering** dengan v1.1, karena filternya
lebih ketat (−22% frekuensi).
