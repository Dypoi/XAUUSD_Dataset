# Auto-Execute MHF-20 — Desain & Audit

Sistem sekarang **mengirim order sungguhan** ke MT5. Dokumen ini menjelaskan bagaimana
setiap mode kegagalan yang Anda khawatirkan ditangani, dan bukti ujinya.

---

## Masalah inti: bukan "order gagal", tapi "order berhasil tapi kita tidak tahu"

Order gagal itu mudah — tinggal ulangi. Yang berbahaya adalah proses mati **setelah**
`order_send` terkirim tapi **sebelum** jawabannya sempat dicatat. Kalau saat restart
sistem asal mengirim ulang, Anda dapat **posisi dobel** — risiko 2× tanpa disadari.

### Solusi: Write-Ahead Intent + identitas unik

```
1. Tulis intent ke SQLite dan COMMIT      <-- sebelum menyentuh MT5
2. Tanam client_id ke comment order + magic number 20250904
3. Kirim order
4. Verifikasi posisi benar-benar ada, baru catat FILLED
```

Mati di titik manapun tetap aman, karena saat startup setiap intent yang statusnya belum
pasti **dicocokkan ke posisi/deal nyata di MT5 lewat `client_id`**. Sistem tidak pernah
mengirim ulang tanpa membuktikan order lama tidak ada.

Lapisan kedua: `UNIQUE(signal_ts, symbol)` di tabel `intents`. **Satu bar sinyal =
maksimal satu order, dijamin oleh database** — bukan oleh logika program yang bisa salah.

### Prinsip RECON-FIRST dan "membeku"

Kalau status sebuah order tidak bisa dipastikan, sistem **membekukan diri**: tidak ada
entry baru sampai rekonsiliasi berhasil. Lebih baik melewatkan peluang daripada
menggandakan posisi. Banner merah muncul di dashboard; klik untuk rekonsiliasi ulang.

---

## Hasil audit — 37/37 LULUS

`python tests/test_execution.py`

| # | Skenario | Hasil |
|---|---|---|
| 1 | Order normal: 1 sinyal → tepat 1 order | LULUS ×3 |
| 2 | **Sinyal sama dikirim 2×** → order kedua ditolak | LULUS ×2 |
| 3 | **Order masuk, jawaban hilang, proses mati** → beku + ORPHAN | LULUS ×4 |
| 4 | **Restart menemukan posisi yatim** → dikenali FILLED, **nol order baru** | LULUS ×5 |
| 5 | Sinyal sama setelah restart → tetap tidak dobel | LULUS ×2 |
| 6 | Broker menolak (retcode fatal) → tidak diulang | LULUS ×4 |
| 7 | **Broker bilang DONE tapi posisi tak terlihat** → beku, tidak menebak | LULUS ×3 |
| 8 | Selama beku, entry baru diblokir total | LULUS |
| 9 | Gerbang risiko: slot, rugi harian, target profit, DD, spread | LULUS ×5 |
| 10 | **Akun REAL terdeteksi → eksekusi diblokir** | LULUS |
| 11 | AutoTrading mati di terminal → diblokir | LULUS |
| 12 | Margin bebas menipis → diblokir | LULUS |
| 13 | Batas 12 order/hari | LULUS |
| 14 | MT5 putus saat mengirim → gagal rapi, tidak crash | LULUS |
| 15 | Integritas DB: nol intent dobel, posisi broker == FILLED | LULUS ×3 |

Uji [3]+[4] adalah yang terpenting: broker tiruan **menerima order lalu melempar
timeout**, proses dimatikan, dan setelah restart sistem menemukan posisi itu tanpa
mengirim satu pun order baru (`2 vs 2`).

### Audit lain tetap hijau
- **Paritas live vs backtest: 191 vs 191 sinyal, 0 selisih**
- **Ketahanan: 25/25** (WAL, kill -9, gap-fill, reconnect, anti-repaint)

**Total 253 pemeriksaan lulus.**

---

## Lapisan pengaman

| Pengaman | Nilai |
|---|---|
| `DEMO_ONLY` | Menolak eksekusi bila akun REAL terdeteksi |
| `MAX_ORDERS_PER_DAY` | 12 (backtest ~2,54/hari — rem bila sinyal meledak) |
| `MAX_CONCURRENT` | 8 slot, risiko total $160 |
| `DAILY_LOSS_LIMIT` | −$300 |
| `DAILY_PROFIT_LIMIT` | +$500 |
| `KILL_SWITCH_DD_PCT` | −20% |
| `MAX_SPREAD_USD` | $1,20 (dicek ulang tepat sebelum kirim) |
| `MIN_FREE_MARGIN` | $200 |
| `MAX_SEND_ATTEMPTS` | 3, retcode fatal tidak diulang |
| `MAX_SLIPPAGE_POINTS` | 30 (~$0,30) |
| Magic number | 20250904 — sistem **hanya** menyentuh posisinya sendiri |

## Manajemen posisi otomatis

Persis seperti backtest: **TP1 di 1R tutup 50% + geser SL ke BE+**, sisanya ke TP 2R,
dan **time-stop 24 jam**. Hanya posisi ber-`client_id` MHF-20 yang disentuh — trade manual
Anda di akun yang sama tidak akan diganggu.

## Kontrol manual di dashboard

- **AUTO ON/OFF** — matikan eksekusi kapan saja, monitoring tetap jalan
- **TUTUP SEMUA** — panic close seluruh posisi MHF-20
- **Banner beku** — klik untuk rekonsiliasi ulang
- **Tab Order** — riwayat setiap intent: PENDING / SENT / FILLED / REJECTED / ORPHAN / ABANDONED

---

## Yang tetap tidak bisa dijamin

1. **Slippage & requote nyata** hanya terlihat saat live. Backtest memakai $0,02.
2. **Swap posisi long menginap** — belum dimodelkan, bisa memakan 40–70% CAGR.
   Ini justru salah satu hal terpenting yang akan diukur 5 hari ini.
3. **5 hari ≈ 10–13 trade.** Terlalu sedikit untuk menyimpulkan profitabilitas.
   Yang diuji: kebenaran eksekusi, kesesuaian spread, dan besaran swap.
4. **Gap akhir pekan** — posisi yang menginap Jumat menanggung risiko gap Senin.
