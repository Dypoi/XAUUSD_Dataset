# Mode Santai — Maksimal 1 Entry Per Hari

Anda minta 1 entry/hari. Sudah jadi, dan **sudah aktif sebagai setelan default**.

---

## Intinya

Sistem lama masuk 2 trade/hari dengan risiko $20 masing-masing. Sekarang: **1 trade/hari,
risiko $100**. Total risiko harian mirip, tapi Anda cuma perlu memantau satu posisi.

| | Standar (v1.1) | **Santai (baru)** |
|---|---|---|
| Entry per hari | 2,03 | **maks 1** (rata-rata 0,31) |
| Total trade 10 thn | 4.905 | **740** |
| Risiko per trade | $20 | **$100** |
| Posisi bersamaan | 8 | **2** |
| Risiko maks terbuka | $800 | **$200** |
| Win rate | 55,33% | **55,27%** |
| Profit Factor | 1,304 | **1,362** |
| Equity 10 thn | $23.881 | $19.482 |
| CAGR | 9,50% | **7,20%** |
| Max Drawdown | −11,68% | **−10,43%** |

**PF naik** (1,304 → 1,362) karena hanya sinyal pertama tiap hari yang diambil, dan
filter jarak diperketat 0,50% → 1,50%. **CAGR turun** dari 9,50% ke 7,20% — itu harga
yang Anda bayar untuk ketenangan.

---

## Satu hal yang harus Anda tahu sejak awal

**Rata-ratanya bukan 1/hari, tapi 0,31/hari.** Ini bukan bug.

Dari 3.110 hari:
- **777 hari (25%) ada sinyal**
- **2.333 hari (75%) tidak ada sinyal sama sekali**

Sinyalnya **menggerombol**: 192 hari punya 8 entry, 168 hari lebih dari 8, tapi 75%
hari kosong total. Membatasi 1/hari memangkas hari sibuk, tapi tidak bisa
"menciptakan" sinyal di hari sepi.

Jadi yang realistis Anda alami: **sekitar 1 trade setiap 3 hari kerja**, kadang beberapa
hari berturut-turut ada, lalu kosong seminggu. Kalau Anda mengharapkan tepat satu trade
setiap hari, Anda akan kecewa — dan lebih berbahaya lagi, tergoda mengendurkan filter.

Kalau ini terasa terlalu sepi, alternatifnya: naikkan `MAX_ENTRIES_PER_DAY` ke 2 atau
turunkan `BIAS_MIN_DIST_PCT` ke 0,50 — tapi Anda kembali ke ~2/hari.

---

## Validasi

| Periode | n | WR | PF | Net |
|---|---|---|---|---|
| IS (2016→2023/02) | 409 | 52,3% | 1,215 | +$2.833 |
| OOS (2023/03→2026) | 344 | 57,8% | **1,482** | +$6.522 |
| Jan–Ags 2026 | 48 | 52,1% | 1,082 | +$180 |

OOS lebih baik dari IS — bukan hasil kurva-fitting.

**Ketahanan biaya** (ini penting karena swap belum dimodelkan):

| Slippage tambahan | PF |
|---|---|
| +$0,00 | 1,350 |
| +$0,20 | 1,291 |
| +$0,50 | **1,176** |

Bahkan pada +$0,50/sisi masih PF 1,176 — jauh lebih tangguh dari v1.0 yang mati (0,728).

**t-stat turun ke +3,77** (dari +8,43). Wajar: 740 trade vs 4.905. Masih di atas ambang
2,0, jadi tetap signifikan — tapi bukti statistiknya lebih tipis.

---

## Setelan yang berubah

```python
MODE                = "santai"
MAX_ENTRIES_PER_DAY = 1        # 0 = tanpa batas (mode standar)
RISK_PER_POSITION   = 100.0    # naik dari $20
MAX_CONCURRENT      = 2        # turun dari 8
BIAS_MIN_DIST_PCT   = 1.50     # naik dari 0,50
MAX_ORDERS_PER_DAY  = 2        # rem keras
```

Kenapa `MAX_CONCURRENT` cuma 2? Karena diuji: 8 slot dan 2 slot memberi hasil hampir
identik (PF 1,350 vs 1,362), tapi 2 slot memotong risiko maksimum terbuka dari $800
ke $200. Tidak ada alasan menahan risiko yang tidak terpakai.

### Kembali ke mode standar

Ubah di `mhf20/live/config.py` **dan** `mhf20/strategy.py` (nilainya wajib sama):

```python
MAX_ENTRIES_PER_DAY = 0
RISK_PER_POSITION   = 20.0
MAX_CONCURRENT      = 8
BIAS_MIN_DIST_PCT   = 0.50
MAX_ORDERS_PER_DAY  = 12
```

---

## Penegakan di sisi live

Batas ini **tidak cuma di backtest**. `executor.py` menolak order kedua di hari yang
sama dengan pesan eksplisit:

> `Mode santai: batas 1 entry/hari sudah terpakai (1). Menunggu besok.`

Tes **[24]** memaksa `MAX_ENTRIES_PER_DAY`, `MAX_CONCURRENT`, dan `RISK_PER_POSITION`
**identik** antara `strategy.py` dan `live/config.py` — kalau suatu saat berbeda, tes
gagal. Tes eksekusi **[13]** membuktikan penolakan itu benar-benar terjadi.

**Audit: paritas 191/191 · resilience 78/78 · eksekusi 38/38.**

---

## Peringatan risiko

Risiko naik 5× per trade ($20 → $100 = **1% dari akun $10.000**). Itu masih konservatif,
tapi artinya **satu SL sekarang terasa 5× lebih sakit**. Dengan win rate 55%, deretan
3–4 rugi beruntun itu normal — siapkan mental untuk −$400 dalam seminggu tanpa ada yang
rusak pada sistemnya.

Sifat dasarnya tidak berubah: reaktif bukan prediktif, rasio menang/kalah ~1,05×, dan
tetap butuh ratusan trade agar edge-nya muncul. Dengan 0,31 trade/hari, 740 trade itu
butuh 10 tahun.
