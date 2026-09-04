# Cara Update MHF-20 ke Versi Terbaru

## Langkah di CMD

### 1. Hentikan program yang sedang jalan
Di jendela CMD tempat MHF-20 berjalan, tekan **Ctrl + C**.

> Kalau `run.bat` menawarkan restart otomatis, tekan **Ctrl + C** sekali lagi
> supaya benar-benar keluar.

### 2. Backup jurnal (opsional tapi disarankan)

```cmd
cd %USERPROFILE%\Desktop\MHF20\mhf20\live
copy data\journal.db %USERPROFILE%\Desktop\journal_backup.db
```

### 3. Ambil versi terbaru

```cmd
cd %USERPROFILE%\Desktop\MHF20
git fetch --depth 1 origin arena/01a067ae-xauusd-dataset
git reset --hard FETCH_HEAD
```

Harus muncul commit terbaru (`HEAD is now at ...`).

> Pakai `fetch` + `reset`, **bukan `git pull`** — clone dangkal tidak punya riwayat
> lengkap sehingga `git pull` gagal.

> `reset --hard` menimpa file program, tapi **jurnal Anda aman**: folder `data\`
> diabaikan Git dan tidak tersentuh.

### 4. Jalankan lagi

```cmd
cd mhf20\live
run.bat
```

Buka **http://127.0.0.1:8765**

---

## Cara memastikan update berhasil

### Cek A — versi kode

```cmd
cd %USERPROFILE%\Desktop\MHF20
git log --oneline -1
```

Harus menampilkan commit terbaru dari daftar di bagian **Riwayat perbaikan**.

### Cek B — jalankan audit

```cmd
cd mhf20\live
.venv\Scripts\python tests\test_resilience.py
```

Harus berakhir dengan **`LULUS 57 · GAGAL 0`**.
Kalau masih 53 atau kurang, berarti update belum masuk.

### Cek C — spread cocok dengan broker

```cmd
.venv\Scripts\python cek_spread.py
```

Sekarang alat ini juga menampilkan **offset server broker**, **contract size**, dan
**lot + risiko nyata**. Yang perlu dicek:
- Spread NYATA mirip iklan Exness (~$0,26) dan status **LOLOS**
- Contract size **100 oz/lot**
- Risiko nyata mendekati **$20**

### Cek D — lihat dashboard

- Candle **bergerak tiap detik**, tidak lagi tersendat ~6 detik
- Harga candle terakhir sekarang **nyambung dengan bid/ask** di header
  (harga candle ada di antara bid dan ask, tidak lagi menempel di bid)

---

## Yang diperbaiki di versi ini

| Bug | Sebelum | Sesudah |
|---|---|---|
| **Candle pakai harga BID** | Semua candle tergeser ~½ spread dari data backtest — bisa membuat sinyal live berbeda dari backtest | Dikonversi ke MID `(bid+ask)/2`, sama persis dengan backtest |
| **Candle tersendat** | Rantai polling 2s + 3s + 1s = **6 detik** | Bar berjalan digerakkan tick tiap **0,25 detik** |
| **Polling lambat** | runner 2s, browser 3s | runner 0,6s, browser 1s |
| **Spread bar 10× lipat** | `spread/100` → `$2,600` pada XAUUSDm (digits=3) → **guard memblokir SEMUA entry** | `spread × point` → `$0,260`, plus jaring pengaman ask-bid |
| **Zona waktu server** | Deteksi otomatis salah baca tick basi saat pasar tutup → offset palsu −12 jam, **merusak Exness yang sudah benar** | `SERVER_GMT_OFFSET = 0` eksplisit untuk Exness (GMT+0 resmi); deteksi otomatis hanya cadangan dengan aturan ketat |
| **Deviation 10× ketat** | `30 point` = $0,03 pada digits=3, bukan $0,30 → sering requote | `MAX_SLIPPAGE_USD` dikonversi via `info.point` |
| **Contract size** | Hardcoded 100 oz | Dibaca dari broker, lot dikoreksi otomatis |
| **Jam tampilan** | Zona laptop (WIB) → beda 7 jam dari MT5, sulit dicocokkan dgn jendela sesi UTC | Semua waktu ditampilkan **UTC**, sama dengan MT5 Exness |

Bug candle-BID adalah yang paling penting. Sinyal MHF-20 membandingkan harga secara
presisi (sweep BSL, break swing high, FVG buffer $0,30), jadi pergeseran setengah spread
bisa memicu atau membatalkan entry yang seharusnya tidak.

Uji regresi [16] dan [17] ditambahkan supaya bug ini tidak terulang.

**Status audit:** paritas 191/191 · ketahanan **57/57** · eksekusi 37/37.
Rincian audit putaran 2: lihat `AUDIT_PUTARAN_2.md`.

### Riwayat perbaikan
- `cbfab5a` candle BID→MID + latensi 6s→1s
- **spread bar 10×** — paling parah: bikin nol entry selama jurnal berjalan

---

## Kalau jurnal ingin dimulai ulang dari hari 1

Update **tidak** mereset hari jurnal. Kalau Anda ingin mulai bersih:

```cmd
cd %USERPROFILE%\Desktop\MHF20\mhf20\live
copy data\journal.db %USERPROFILE%\Desktop\journal_lama.db
del data\journal.db
run.bat
```

> Posisi yang masih terbuka di MT5 tetap ada. Tutup manual dulu di MT5 kalau
> ingin benar-benar mulai dari nol.
