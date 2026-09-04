# Audit Forensik Putaran 2 — Batas MT5

## Jawaban jujur atas pertanyaan "apakah sudah benar-benar diaudit?"

**Belum, sampai audit ini.** Audit sebelumnya (parity, resilience, execution) menguji
**logika internal**: apakah sinyal live sama dengan backtest, apakah data selamat dari
crash, apakah order tidak dobel. Semua itu valid dan tetap lulus.

Yang **tidak** diuji secara sistematis adalah **batas antara sistem dan MT5** — tempat
angka mentah broker diterjemahkan menjadi angka yang dipakai strategi. Dua bug lolos di
sana (`WARMUP_BARS`, spread 10×), keduanya ditemukan oleh Anda, bukan oleh audit saya.
Karena dua kali gagal dengan pola sama, seluruh permukaan itu disisir ulang.

Pola bug-nya selalu sama: **satuan atau asumsi lingkungan yang tidak diverifikasi ke broker.**

---

## Temuan putaran 2 — 3 bug baru

### 🔴 BUG 3 — Zona waktu server broker (paling merusak)

Bar dari MT5 ber-timestamp **waktu server broker**, bukan UTC. Exness umumnya
**GMT+2/+3** dan ikut DST. Sinyal MHF-20 memakai jendela sesi berbasis UTC
(Asia `<7`, London `7–12`).

Dampak diukur dengan backtest 10 tahun:

| Offset server | Sinyal | Cocok dengan baseline UTC |
|---|---|---|
| GMT+0 (benar) | 11.374 | 100% |
| GMT+2 | 11.371 | **83,6%** |
| GMT+3 | 12.115 | **80,9%** |

**~19% sinyal berbeda** dari yang divalidasi backtest. Ini bukan penyimpangan kecil —
BSL/SSL dihitung dari jendela sesi yang salah.

**Perbaikan:** `_detect_server_offset()` membandingkan `tick.time` (server) dengan jam
UTC nyata saat connect, lalu semua timestamp bar dikonversi ke UTC. Otomatis benar
walau broker pindah DST.

### 🔴 BUG 4 — Deviation slippage 10× terlalu ketat

`MAX_SLIPPAGE_POINTS = 30` dengan komentar "~$0,30". Tapi `deviation` MT5 bersatuan
**point**, dan XAUUSDm `digits=3` → `point=0.001`:

| | perhitungan | hasil |
|---|---|---|
| Niat | — | $0,30 |
| Nyata (digits=3) | `30 × 0,001` | **$0,03** |

Toleransi 10× lebih ketat dari yang dimaksud → order sering kena requote/ditolak saat
harga bergerak cepat, justru pada momen displacement yang menjadi inti setup ini.

**Perbaikan:** `MAX_SLIPPAGE_USD = 0.30`, dikonversi ke point via `info.point`.

### 🟡 BUG 5 — Contract size diasumsikan 100 oz

`CONTRACT_SIZE = 100.0` di-hardcode dan tidak pernah dicocokkan ke broker. Kalau akun
Anda memakai kontrak berbeda (mis. cent account), **seluruh perhitungan lot salah** dan
risiko per posisi tidak lagi $20.

**Perbaikan:** executor membaca `trade_contract_size` dan mengoreksi lot bila berbeda,
sambil mencatat peringatan.

---

## Status audit setelah perbaikan

| Audit | Sebelum | Sesudah |
|---|---|---|
| Paritas live vs backtest | 191/191 | **191/191** |
| Ketahanan & lingkungan | 37/37 | **45/45** |
| Eksekusi order | 37/37 | **37/37** |

Uji baru: **[19]** deviation dari USD · **[20]** offset zona waktu · **[21]** contract size.

---

## Riwayat seluruh bug yang ditemukan

| # | Bug | Akibat kalau lolos | Ditemukan oleh |
|---|---|---|---|
| 1 | `WARMUP_BARS` 4.000 < 11.520 | Bias H4 selalu False → **nol entry** | audit paritas |
| 2 | Candle BID, bukan MID | Sinyal bergeser ½ spread | **Anda** |
| 3 | Spread bar `/100` | `$2,600` → guard blokir **semua entry** | **Anda** |
| 4 | Zona waktu server | **~19% sinyal berbeda** | audit putaran 2 |
| 5 | Deviation 10× ketat | Requote saat displacement | audit putaran 2 |
| 6 | Contract size hardcoded | Risiko per posisi salah | audit putaran 2 |

Empat dari enam adalah **kesalahan satuan/asumsi lingkungan di batas MT5**, bukan
kesalahan logika strategi. Itulah kelas bug yang paling sulit terlihat: sistem tampak
berjalan normal, tapi diam-diam melakukan hal yang salah.

---

## Verifikasi mandiri

```cmd
.venv\Scripts\python cek_spread.py
```

Sekarang menampilkan seluruh parameter lingkungan: digits, point, spread nyata vs
konversi, **offset server broker**, toleransi slippage dalam point, **contract size**,
**lot dan risiko nyata** yang akan dipakai, serta stops level minimum. Bandingkan
sendiri dengan yang diiklankan Exness.

---

## Batas kejujuran audit ini

Yang **sudah** dibuktikan: logika sinyal identik backtest, data tahan crash, order tidak
mungkin dobel, dan parameter lingkungan kini dibaca dari broker.

Yang **belum bisa** dibuktikan dari sini — dan hanya terlihat saat live:
1. **Slippage & requote nyata** pada eksekusi Exness
2. **Swap** posisi long menginap (Exness mengiklankan −$0,53/lot/malam — pada 8 posisi
   paralel ini bisa memakan 40–70% CAGR)
3. **Perilaku saat rollover & rilis berita** dengan spread melebar

Ketiganya justru alasan utama jurnal 5 hari ini dijalankan.
