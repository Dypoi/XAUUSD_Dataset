# Audit Forensik — MHF-20 Live Journal

Dijalankan sebelum jurnal 5 hari. Semua uji dapat diulang:

```
python tests/test_parity.py       # paritas live vs backtest
python tests/test_resilience.py   # ketahanan crash / offline
```

---

## A. Paritas mesin: live vs backtest — **LULUS**

Data historis diputar ulang bar-per-bar lewat mesin **live** (hanya bar tertutup, hanya
data masa lalu pada tiap titik), lalu sinyalnya dibandingkan dengan mesin **backtest**.

| | |
|---|---|
| Bar dibandingkan | 4.000 |
| Sinyal backtest | **191** |
| Sinyal live | **191** |
| Ketidakcocokan | **0** |

Artinya angka backtest (PF 1,213) memang berlaku untuk sistem yang akan Anda jalankan.

### 🔴 BUG KRITIS DITEMUKAN DI SINI

Uji paritas pertama "lulus" dengan 0 vs 0 sinyal — lulus semu. Setelah dipaksa memakai
segmen padat sinyal, ketahuan: **`WARMUP_BARS` awalnya 4.000 bar, padahal MA240 pada H4
butuh 240 × 48 = 11.520 bar M5.** Akibatnya bias H4 **selalu `False`** dan sistem
**tidak akan pernah entry sama sekali** selama 5 hari.

Diperbaiki → `WARMUP_BARS = 26000`. Uji nomor [9] sekarang menjaga invarian ini permanen.

---

## B. Ketahanan — **25 / 25 LULUS**

| # | Uji | Hasil |
|---|---|---|
| 1 | `journal_mode=WAL`, `synchronous=FULL` | LULUS |
| 2 | Bar/sinyal/trade idempotent (reconnect tidak menggandakan) | LULUS ×3 |
| 3 | Simulasi `kill -9`: DB terbuka, trade OPEN selamat, state jurnal selamat, heartbeat selamat | LULUS ×4 |
| 4 | Hari jurnal dihitung dari waktu nyata (tidak reset ke hari 1) | LULUS |
| 5 | Rekonsiliasi trade yang tertutup saat program mati | LULUS ×2 |
| 6 | Semua panggilan MT5 aman saat terminal mati (return `None`/`[]`, tidak crash) | LULUS |
| 7 | Anti-repaint: sinyal hanya dari bar tertutup | LULUS ×2 |
| 8 | Order hanya lewat `executor.py`; intent ditulis sebelum kirim; UNIQUE per bar; client_id di comment; verifikasi pasca-kirim; proteksi akun real | LULUS ×6 |
| 9 | `WARMUP_BARS` ≥ kebutuhan MA240 H4 (26.000 ≥ 11.520) | LULUS |
| 10 | Guardrail memblokir: slot penuh, limit rugi harian, kill-switch DD | LULUS ×3 |

## C. Uji end-to-end sungguhan

Server dijalankan, lalu **dibunuh paksa dengan `kill -9`** (meniru baterai habis) —
meninggalkan WAL belum ter-checkpoint, kondisi terburuk.

**Sebelum crash:** 2.000 bar · 14 sinyal
**Setelah restart:** 2.000 bar · 14 sinyal

```
PRAGMA integrity_check : ok
bar duplikat           : 0
sinyal duplikat        : 0
```

Log pemulihan: `Melanjutkan jurnal hari ke-1 dari 5` · `Gap-fill: 26.001 bar, 0 baru`
→ melanjutkan, bukan mengulang; tanpa duplikasi.

**Ctrl+C (SIGINT)** menghasilkan urutan shutdown yang benar:
`Sinyal berhenti diterima → Loop berhenti bersih → Bersih.`

---

## D. Skenario gangguan & penanganannya

| Kejadian | Yang terjadi |
|---|---|
| **Ctrl+C / tutup jendela** | Shutdown bersih, state tersimpan, `run.bat` restart otomatis 5 detik |
| **Laptop mati / baterai habis** | WAL menjamin commit terakhir utuh; restart memulihkan semuanya |
| **Internet putus** | Bridge auto-reconnect (backoff 2→30 dtk); banner merah; DB tetap aman |
| **MT5 ditutup / logout** | Semua panggilan return aman; status `RECONNECTING`; nol crash |
| **Laptop tidur lalu bangun** | Gap-fill menarik bar yang terlewat; rekonsiliasi menyamakan posisi |
| **Anda tutup 1 hari penuh** | Hari jurnal dihitung dari `start_ts` nyata, bukan dari uptime |
| **Trade tertutup saat offline** | `deals_since()` menemukan hasilnya, PnL tercatat, status jadi CLOSED |
| **Buka dashboard 2 tab** | Keduanya read-only ke DB yang sama; aman |
| **Spread melebar ekstrem** | Guard `spread ≤ $1,20` menolak entry, alasannya tercatat |

---

## E. Batasan yang diakui jujur

1. **Auto-execute aktif** — audit jalur order ada di `EKSEKUSI_OTOMATIS.md` (37/37 lulus,
   termasuk skenario order-masuk-tapi-jawaban-hilang).
2. **Slippage/requote nyata** hanya terukur saat live; backtest memakai $0,02.
3. **5 hari ≈ 10–13 trade.** Terlalu sedikit untuk menilai profitabilitas
   (edge +0,100R butuh ratusan trade). Jurnal ini menguji **eksekusi dan kepatuhan**,
   bukan membuktikan strategi. Lihat `../docs/HONEST_LIMITS.md`.
4. **Mode replay memakai data historis** — untuk latihan UI, bukan simulasi broker.
