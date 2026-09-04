# Cara Download & Menjalankan MHF-20 di Laptop Windows

Semua lewat **CMD** (Command Prompt). Ikuti berurutan.

---

## Persiapan (sekali saja)

### 1. Pasang Git
Download di **https://git-scm.com/download/win** → install dengan pilihan default.

### 2. Pasang Python 3.11 atau 3.12
Download di **https://www.python.org/downloads/windows/**

> ⚠️ **PENTING:** di layar pertama installer, centang **"Add python.exe to PATH"**.
> Kalau terlewat, semua perintah `python` di bawah akan gagal.

> ⚠️ **Jangan pakai Python 3.13** — paket `MetaTrader5` belum tentu tersedia untuk versi itu.

### 3. Cek keduanya terpasang

Buka **CMD** (tekan `Win + R`, ketik `cmd`, Enter):

```cmd
git --version
python --version
```

Harus muncul nomor versi. Kalau muncul `'git' is not recognized`, tutup CMD, buka lagi
(PATH baru terbaca setelah CMD dibuka ulang).

---

## Download (pilih SATU cara)

### Cara A — Hanya folder trading (DISARANKAN, ~800 KB)

Repo ini berisi 451 MB data CSV yang **tidak dibutuhkan untuk trading**.
Perintah di bawah **sudah diuji** dan hanya mengunduh folder `mhf20`:

```cmd
cd %USERPROFILE%\Desktop

git clone --filter=blob:none --no-checkout --depth 1 --branch arena/01a067ae-xauusd-dataset https://github.com/Dypoi/XAUUSD_Dataset.git MHF20

cd MHF20

git sparse-checkout init --no-cone

git sparse-checkout set "/mhf20/"

git checkout

cd mhf20\live
```

Hasil: **824 KB** (dibanding 582 MB kalau clone biasa). Sekarang Anda di folder yang benar.

> **Kenapa serumit ini?** Perintah `git sparse-checkout` versi biasa (mode *cone*) tetap
> menarik semua file di folder root — termasuk 10 file CSV. Kombinasi
> `--no-checkout` + `--no-cone` adalah yang benar-benar mengecualikannya.


### Cara B — Seluruh repo (451 MB, lama)

Hanya kalau Anda juga mau data CSV untuk riset:

```cmd
cd %USERPROFILE%\Desktop
git clone --branch arena/01a067ae-xauusd-dataset https://github.com/Dypoi/XAUUSD_Dataset.git MHF20
cd MHF20\mhf20\live
```

### Cara C — Tanpa Git (download ZIP)

1. Buka: `https://github.com/Dypoi/XAUUSD_Dataset/tree/arena/01a067ae-xauusd-dataset`
2. Tombol hijau **Code** → **Download ZIP**
3. Ekstrak, lalu di CMD:
   ```cmd
   cd %USERPROFILE%\Desktop\XAUUSD_Dataset-arena-01a067ae-xauusd-dataset\mhf20\live
   ```

> Kekurangan cara C: tidak bisa `git pull` untuk update.

---

## Jalankan

Pastikan **MetaTrader 5 sudah terbuka dan login ke akun demo Exness** lebih dulu.

Di CMD, dari dalam folder `mhf20\live`:

```cmd
run.bat
```

Saat pertama kali, script otomatis membuat virtual environment dan memasang semua
dependensi (butuh 2–5 menit, perlu internet). Setelah itu buka browser ke:

**http://127.0.0.1:8765**

### Kalau mau manual (tanpa run.bat)

```cmd
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python app.py
```

---

## Sebelum hari-1: 3 pemeriksaan wajib

### 1. Cek MT5 bisa dibaca Python

```cmd
.venv\Scripts\python -c "import MetaTrader5 as m; print(m.initialize()); print(m.account_info())"
```

Harus muncul `True` dan data akun Anda. Kalau `False`:
- MT5 belum terbuka, **atau**
- **Tools → Options → Expert Advisors → Allow automated trading** belum dicentang

### 2. Cek nama simbol emas Anda

```cmd
.venv\Scripts\python -c "import MetaTrader5 as m; m.initialize(); print([s.name for s in m.symbols_get() if 'XAU' in s.name.upper()])"
```

Exness biasanya `XAUUSDm`. Kalau nama Anda berbeda, edit `config.py` baris `SYMBOL`.
(Sistem juga mencoba menebak otomatis, tapi lebih aman dipastikan.)

### 3. Latihan dulu tanpa MT5 (mode replay)

```cmd
set MHF20_MODE=replay
.venv\Scripts\python app.py
```

Memutar data historis supaya Anda hafal tampilan dashboard sebelum uang (demo) berjalan.
Tutup dengan Ctrl+C, lalu jalankan `run.bat` untuk mode sungguhan.

> Mode replay butuh file cache yang tidak ikut di-download. Kalau error, lewati saja
> langkah ini — tidak wajib.

---

## Perintah harian

| Tujuan | Perintah |
|---|---|
| Mulai / lanjut jurnal | `run.bat` |
| Berhenti | `Ctrl + C` di jendela CMD |
| Buka dashboard | browser → `http://127.0.0.1:8765` |
| Ambil update terbaru | `git pull origin arena/01a067ae-xauusd-dataset` (dari folder `MHF20`) |
| Jalankan audit | `.venv\Scripts\python tests\test_execution.py` |

**Aman ditutup kapan saja.** Data tersimpan di `data\journal.db`. Saat dijalankan lagi,
jurnal lanjut di hari yang benar — bukan mulai dari nol.

---

## Kalau bermasalah

| Gejala | Sebab & solusi |
|---|---|
| `'git' is not recognized` | Git belum terpasang, atau CMD perlu dibuka ulang |
| `'python' is not recognized` | Saat install Python, "Add to PATH" tidak dicentang. Install ulang |
| `No module named MetaTrader5` | Anda pakai Python 3.13 atau bukan Windows. Pakai 3.11/3.12 |
| `m.initialize()` → `False` | MT5 belum dibuka, atau AutoTrading belum diaktifkan |
| Port 8765 dipakai | `set MHF20_PORT=8899` lalu jalankan lagi |
| Dashboard kosong | Tunggu 1–2 menit; sistem menarik 26.000 bar historis dulu |
| Banner merah "DIBEKUKAN" | Normal — pengaman anti-dobel. Klik banner untuk rekonsiliasi |
| Tidak ada sinyal seharian | Wajar. Rata-rata 2,5/hari dan **hanya 39% hari punya entry** |

---

## Backup jurnal Anda

File `data\journal.db` berisi seluruh hasil 5 hari. Salin sesekali:

```cmd
copy data\journal.db %USERPROFILE%\Desktop\journal_backup.db
```

Ekspor semua data lewat browser: **http://127.0.0.1:8765/api/export**

---

## Ringkas — copy-paste sekali jalan

```cmd
cd %USERPROFILE%\Desktop
git clone --filter=blob:none --no-checkout --depth 1 --branch arena/01a067ae-xauusd-dataset https://github.com/Dypoi/XAUUSD_Dataset.git MHF20
cd MHF20
git sparse-checkout init --no-cone
git sparse-checkout set "/mhf20/"
git checkout
cd mhf20\live
run.bat
```

Lalu buka **http://127.0.0.1:8765**
