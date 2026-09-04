# MHF-20 · Jurnal Trading Live (5 Hari)

Dashboard lokal untuk menjalankan jurnal MHF-20 di laptop Anda, membaca MetaTrader 5.

> **AUTO-EXECUTE AKTIF.** Sistem mengirim order sungguhan ke MT5, mengelola TP1/BE/
> time-stop, dan mencatat semuanya. Dirancang agar **tidak mungkin menggandakan posisi**
> walau laptop mati tepat saat order dikirim — lihat `EKSEKUSI_OTOMATIS.md`.
> `DEMO_ONLY=True` menolak eksekusi bila mendeteksi akun REAL.

---

## Cara pakai (Windows + Exness demo)

1. Buka **MetaTrader 5**, login ke akun **demo Exness**.
2. Pastikan **XAUUSDm** ada di *Market Watch* (klik kanan → Show All bila belum).
3. Aktifkan **Tools → Options → Expert Advisors → Allow automated trading**
   (wajib — tanpa ini order akan ditolak).
4. Klik dua kali **`run.bat`**.
5. Buka **http://127.0.0.1:8765**

Instalasi dependensi berjalan otomatis saat pertama kali.

### Berhenti
Tekan **Ctrl+C**. State tersimpan. Jalankan `run.bat` lagi untuk melanjutkan —
jurnal lanjut di hari yang benar, bukan reset ke hari 1.

---

## Isi dashboard

| Panel | Isi |
|---|---|
| **Header** | Status sistem, koneksi MT5, hari ke-N/5, bid/ask/spread live, equity, PnL hari ini, slot terpakai |
| **Chart M5** | Candle update ~per detik, garis BSL / SSL / MA240-H4, penanda ▲ sinyal valid dan · sinyal ditolak |
| **Kenapa entry / kenapa tidak** | **9 syarat**, tiap baris: lolos/gagal, nilai konkret, dan alasan mengapa syarat itu ada |
| **Ringkasan jurnal** | Trade, win rate, PF, net, ekspektasi ($ dan R), sinyal valid vs ditolak |
| **Tab Posisi/Sinyal/Order/Trade/Log** | Posisi live, riwayat sinyal, **status tiap order (intent)**, trade, log |
| **Tombol kontrol** | AUTO ON/OFF · TUTUP SEMUA (panic close) · banner beku (klik = rekonsiliasi) |

Contoh baris alasan yang tercatat:

```
NO  Sweep BSL          high[-1]=4790.77 / high[-2]=4789.66 vs BSL=4838.63
                       Likuiditas sisi beli harus sudah disapu.
NO  Bias H4 bullish    close_H4 vs MA240 = DI BAWAH
                       Long-only searah tren menengah. Short terbukti rugi (PF 0,748).
OK  Spread <= $1.2     spread=$0.610
                       Spread lebar memakan edge yang cuma +0,47pp.
```

---

## Ketahanan

Diuji langsung, bukan diklaim — lihat **`AUDIT_FORENSIK.md`**.

- **Ctrl+C / tutup jendela** → shutdown bersih, `run.bat` restart otomatis
- **Laptop mati mendadak** → SQLite WAL + `synchronous=FULL`; diuji dengan `kill -9`,
  data identik sebelum/sesudah, `integrity_check: ok`, nol duplikat
- **Internet putus / MT5 tertutup** → auto-reconnect backoff, banner merah, nol crash
- **Offline lalu kembali** → gap-fill bar yang terlewat + rekonsiliasi posisi & deal
- **Hari jurnal** dihitung dari waktu nyata, tahan terhadap berapa lama pun program mati

---

## Mode latihan (tanpa MT5)

```bash
MHF20_MODE=replay python app.py
```

Memutar data historis. Berguna untuk membiasakan diri dengan dashboard sebelum hari-1.

---

## Ekspektasi jujur untuk 5 hari

Dengan 2,54 entry/hari → sekitar **10–13 trade**. Ekspektasi backtest **+0,100R/trade**,
jadi harapan teoretisnya hanya **≈ +1,2R (~$24)** — dan sebaran acaknya jauh lebih lebar
dari itu. **Lima hari tidak bisa membuktikan atau menggugurkan strategi ini.**

Yang benar-benar diuji dalam 5 hari:
1. Apakah sinyal muncul pada frekuensi yang diharapkan (~2,5/hari)?
2. Apakah spread & slippage Exness sesuai asumsi backtest ($0,337 median)?
3. Berapa besar **swap** pada posisi long yang menginap? (risiko terbesar yang belum dimodelkan)
4. Apakah eksekusi otomatis berjalan benar: lot tepat, SL/TP terpasang, TP1 & BE jalan?

Nilai keberhasilan dari **kebenaran eksekusi**, bukan dari PnL.

---

## Berkas

```
config.py          satu-satunya sumber parameter
executor.py        pengiriman order + write-ahead intent + rekonsiliasi
signal_engine.py   mesin sinyal (terbukti identik dengan backtest)
store.py           SQLite WAL, idempotent, crash-safe
mt5_bridge.py      koneksi MT5 read-only + auto-reconnect (+ ReplayBridge)
runner.py          loop utama: recovery, gap-fill, rekonsiliasi
app.py             server FastAPI + WebSocket
static/index.html  dashboard (canvas murni, nol dependensi internet)
tests/             audit forensik
```
