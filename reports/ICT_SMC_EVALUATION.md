# Evaluasi Kuantitatif: ICT / SMC / Price Action vs Dataset XAUUSD 10 Tahun

**Catatan:** Kedua PDF (`Playbook_ICT_SMC_PA.pdf`, `Anatomi_ICT_SMC.pdf`) **tidak sampai** ke workspace saya — folder upload kosong. Evaluasi ini menguji **primitif inti ICT/SMC yang falsifiable** terhadap dataset yang sama (3.54 juta bar M1, 2016–2026), bukan isi spesifik dokumen Anda. Silakan lampirkan ulang untuk review yang presisi.

Biaya round-turn yang dipakai: **3.6 bps** (spread median aktual dataset 1.8 bps × 2 sisi).

---

## Ringkasan Vonis

| Konsep ICT/SMC | Edge kotor | **Edge NET** | Vonis |
|---|---|---|---|
| Fair Value Gap (M5) | +0.09 s/d +0.90 bps | **−2.70 s/d −3.51** | ❌ Gagal |
| Fair Value Gap (M15) | +0.45 s/d +3.20 bps | **−0.40 s/d −3.15** | ❌ Gagal |
| Liquidity Sweep / Judas Swing | **arah terbalik** | **−4.08 s/d −6.70** | ❌❌ Gagal total |
| Order Block retest (kausal) | −0.13 s/d +0.15 bps | **−3.45 s/d −4.98** | ❌ Gagal |
| Killzone (London/NY/Silver Bullet) | t-stat 0.13–1.63 | tidak signifikan | ❌ Gagal |

**Tidak ada satu pun primitif ICT/SMC yang bertahan setelah biaya bid/ask nyata pada XAUUSD.**

---

## 1. Temuan Terpenting: Saya Menemukan Look-Ahead Bias — di Kode Saya Sendiri

Ini bagian yang paling instruktif dari seluruh analisis, dan alasan utama saya menulis dokumen ini.

Pengujian Order Block pertama saya menghasilkan:

```
Retest Bullish OB -> long    n=17018   h6: gross +13.13 bps  net +9.53  (t = +55.1)
Retest Bearish OB -> short   n=16586   h6: gross +12.75 bps  net +9.15  (t = +50.6)
```

**t-stat 55.** Sharpe implisit di atas 8. Ini akan terlihat seperti mesin uang.

Saya tidak percaya, dan menjalankan uji simetri: apa yang terjadi kalau sinyal yang sama saya balik arahnya?

```
Retest Bullish OB -> LONG  [BOCOR]   gross +13.13 (t +55.1)
Retest Bullish OB -> SHORT [BOCOR]   gross -13.13 (t -55.1)
```

Dua-duanya "bekerja" secara ekstrem dan simetris sempurna. **Itu mustahil secara struktural.** Penyebabnya ada di satu baris:

```python
imp_up = (b.c.shift(-3) - b.c) > 1.5*atr   # shift(-3) = MELIHAT 3 BAR KE MASA DEPAN
```

Saya mendefinisikan "Order Block" sebagai bar yang **diikuti** impulse — tapi informasi "diikuti impulse" baru tersedia *setelah* impulse terjadi. Zona OB-nya jadi menandai lokasi yang sudah dipastikan menguntungkan.

**Setelah diperbaiki jadi kausal penuh** (impulse dikonfirmasi 3 bar sebelum sinyal, plus `shift(1)`):

```
Retest Bullish OB -> LONG  [KAUSAL]   n=7980   h6: gross -0.13 bps  net -3.73  (t -0.4)
Retest Bearish OB -> SHORT [KAUSAL]   n=7786   h6: gross -0.72 bps  net -4.32  (t -2.3)
```

**Dari +13 bps menjadi −0.13 bps.** Seluruh "edge" adalah kebocoran informasi. Dan kontrol final:

```
Retest zona ACAK -> LONG    n=5170   h6: gross +0.47 bps  (t +1.3)
```

**Zona yang dipilih dengan angka acak berkinerja LEBIH BAIK (+0.47) daripada Order Block "asli" (−0.13).**

### Kenapa ini krusial untuk Anda

Order Block, Breaker Block, Mitigation Block, dan sebagian besar konsep SMC **didefinisikan secara retrospektif** — "bar terakhir sebelum pergerakan impulsif". Definisi itu sendiri mengandung masa depan. Saat Anda menandainya di chart historis, Anda sudah tahu impulse-nya terjadi. Saat trading live, **Anda tidak tahu**.

Inilah mekanisme persis kenapa ICT/SMC terlihat begitu meyakinkan di backtest visual dan begitu sulit di akun live. Bukan karena "eksekusi Anda kurang disiplin" — tapi karena **edge-nya tidak pernah ada sejak awal**; ia artefak dari cara konsepnya didefinisikan.

Saya menemukan bug ini di kode saya sendiri dalam hitungan menit karena saya menjalankan uji simetri dan uji kontrol acak. Backtest visual manual di TradingView tidak punya pengaman itu.

---

## 2. Liquidity Sweep / Judas Swing — Arahnya Justru Terbalik

Ini hasil paling telak. Premis ICT: harga menyapu likuiditas di atas high sesi Asia (stop hunt), lalu **berbalik turun**.

| Setup | n | h6 gross | h48 gross | t-stat |
|---|---|---|---|---|
| Sweep Asian HIGH → short (London KZ) | 3,140 | −0.65 | **−2.34** | −3.3 |
| Sweep Asian LOW → long (London KZ) | 2,754 | −0.48 | **−3.10** | −3.5 |
| Sweep Asian HIGH → short (NY KZ) | 3,160 | −0.49 | −1.05 | −1.2 |
| Sweep Asian LOW → long (NY KZ) | 2,906 | −1.12 | **−1.82** | −2.0 |

Angka negatif = **strategi rugi bahkan sebelum biaya**. Dan ini signifikan secara statistik (t = −3.3, −3.5).

Artinya: setelah harga menyapu high Asia lalu close kembali di bawahnya, harga cenderung **melanjutkan naik**, bukan reversal. Emas melanjutkan momentum breakout, tidak memberi "reversal Judas". Konsep ini bukan sekadar netral — **ia salah arah secara sistematis**.

---

## 3. Fair Value Gap — Edge Nyata, Tapi 4× Terlalu Kecil

FVG adalah satu-satunya konsep dengan sinyal statistik yang benar-benar ada:

| Setup | n | h24 gross | h48 gross | t-stat h48 |
|---|---|---|---|---|
| M5 FVG bullish → long | 88,794 | +0.54 | +0.90 | **+6.3** |
| M15 FVG bullish → long | 15,741 | +1.97 | **+3.20** | **+5.7** |
| M5 FVG bearish → short | 84,938 | −0.61 | −0.84 | −5.8 |
| M15 FVG bearish → short | 14,477 | −1.16 | −2.27 | −3.6 |

t-stat +6.3 dengan 88 ribu sampel — itu **edge yang sah secara statistik**. Imbalance memang punya kandungan informasi.

Masalahnya: edge terbaik = **+3.20 bps** (M15, hold 48 bar = 12 jam). Biaya = **3.6 bps**. Net = **−0.40 bps**.

Anda benar tentang keberadaan fenomenanya. Pasar hanya tidak memberi cukup ruang untuk memanennya. Butuh spread **di bawah 1.5 bps** agar FVG M15 impas — itu wilayah institusional, bukan retail.

Catatan: **FVG bearish → short justru rugi lebih besar** (−5.87 net). Sisi short tidak simetris karena drift struktural emas positif.

---

## 4. Killzone — Jam ICT Bukan Jam Terbaik

| Killzone | mean/jam | t-stat | Return ann. | Tahun positif |
|---|---|---|---|---|
| London KZ 07–10 | +0.150 bps | +0.74 | +1.16% | 6/11 |
| NY AM KZ 12–15 | −0.162 bps | −0.46 | **−1.25%** | 5/11 |
| London Close 15–17 | −0.118 bps | −0.34 | −0.61% | 5/11 |
| Asian KZ 00–03 | +0.371 bps | +1.63 | +2.87% | 7/11 |
| **Silver Bullet 14–15** | −0.081 bps | **−0.13** | −0.21% | 7/11 |

Tidak ada yang mencapai signifikansi (semua |t| < 1.7). "Silver Bullet" — killzone paling terkenal — punya t-stat **−0.13**, yang secara statistik tidak bisa dibedakan dari lemparan koin.

**Bandingkan dengan temuan riset saya sebelumnya:**

| Jendela | Return ann. | t-stat | Tahun positif |
|---|---|---|---|
| Semua killzone ICT | −1.25% s/d +2.87% | 0.13–1.63 | 5–7 dari 11 |
| **20:00–24:00 UTC (bukan killzone ICT)** | **+9.65%** | **+5.86** | **11/11** ✅ |

Jendela waktu dengan edge terkuat di seluruh dataset — konsisten di **setiap tahun tunggal** — sama sekali tidak ada dalam kerangka ICT. Sementara jam-jam yang dipromosikan ICT tidak menunjukkan apa-apa.

---

## 5. Kenapa Semua Ini Gagal: Satu Angka

| | Nilai |
|---|---|
| Spread median XAUUSD | $0.337 |
| ATR M5 median | $0.669 |
| **Spread sebagai % ATR M5** | **50%** |

Setiap trade intraday XAUUSD dimulai dengan kerugian setara **setengah pergerakan normal 5 menit**. Ini bukan kritik terhadap ICT secara khusus — ini kendala yang membunuh **semua** metodologi entry-presisi frekuensi tinggi di instrumen ini, termasuk strategi scalping mean-reversion saya sendiri yang punya t-stat 5–7 dan tetap gagal (avg R = −0.99).

Yang menentukan profitabilitas di XAUUSD bukan kualitas entry — tapi **seberapa jarang Anda menyentuh pasar.**

---

## 6. Apa yang Sebenarnya Bisa Diselamatkan dari Kerangka ICT

Saya tidak menyarankan membuang semuanya. Tiga hal punya nilai riil:

1. **Struktur → arah, bukan entry.** Konsep market structure (HH/HL vs LH/LL) pada dasarnya adalah *trend following*. Pada horizon **mingguan–bulanan**, itu terbukti bekerja — persis itu yang jadi inti XAU-TRV (Sharpe 1.00). Kesalahannya adalah menerapkannya di M5/M15 di mana biaya membunuhnya.
2. **Manajemen risiko & R-multiple.** Disiplin ICT soal risk:reward dan position sizing itu solid dan universal.
3. **Kesadaran likuiditas.** Memahami di mana stop menumpuk berguna untuk **penempatan SL** (jangan taruh tepat di bawah swing low yang obvious), meski bukan sebagai sinyal entry.

**Yang harus dibuang:** Order Block, Breaker, Mitigation Block sebagai sinyal entry — semuanya cacat definisi retrospektif. Judas Swing — terbukti terbalik arah. Killzone — tidak signifikan.

---

## 7. Perbandingan Langsung

| | ICT/SMC (versi terbaik: FVG M15) | XAU-TRV |
|---|---|---|
| Edge kotor | +3.20 bps/trade | rendah per bar |
| Biaya | 3.6 bps/trade | **0.19%/tahun total** |
| **Net** | **−0.40 bps** ❌ | **Sharpe 1.004** ✅ |
| Trade/tahun | ~1,500 | rebalance 12× |
| Tahan biaya? | Mati di spread 1× | Sharpe 0.97 di spread **3×** |
| Look-ahead risk | **Tinggi** (definisi retrospektif) | Terverifikasi bersih |

---

## 8. Rekomendasi

**Untuk akun retail XAUUSD, ICT/SMC tidak layak dijalankan sebagai sistem entry.** Bukan karena konsepnya "salah" secara filosofis — FVG terbukti punya kandungan informasi nyata (t=6.3) — tapi karena:

1. Magnitudo edge (0.5–3.2 bps) **di bawah biaya transaksi** (3.6 bps)
2. Beberapa konsep inti (Judas Swing) **terbukti berlawanan arah**
3. Konsep sentralnya (Order Block) **secara definisi mengandung look-ahead bias**

**Kalau Anda tetap ingin menjalankannya**, syarat minimum yang bisa saya dukung secara data:
- Timeframe **H1 ke atas**, jangan M5/M15
- Spread broker **< 1.5 bps** (raw ECN, bukan standard account)
- Maksimal **5–10 trade/bulan**
- Long-bias — sisi short konsisten lebih buruk di dataset ini
- **Forward-test 6 bulan** dengan pencatatan setiap trade sebelum menaikkan size

**Rekomendasi utama saya tetap XAU-TRV.** Ia menang bukan karena sinyalnya lebih pintar — sinyalnya justru jauh lebih lemah dari FVG. Ia menang karena **hanya rebalance 12 kali setahun**, sehingga edge kecil pun bisa bertahan.

---

## Lampiran: Reproduksi

| File | Isi |
|---|---|
| `research/ict_test.py` | Uji 4 primitif ICT/SMC |
| `research/ob_fix.py` | **Demonstrasi look-ahead bias + versi kausal + kontrol acak** |

Jalankan: `python research/ict_test.py && python research/ob_fix.py`

Saya sarankan menjalankan `ob_fix.py` sendiri — melihat +13 bps runtuh jadi −0.13 bps setelah satu baris diperbaiki adalah pelajaran yang lebih kuat daripada tabel mana pun.

---
---

# ADENDUM — Ronde 2: Uji Setup ICT Lanjutan + Kontrol Drift

*(Ditambahkan setelah percobaan lampiran PDF kedua. File tetap tidak sampai ke workspace — pengujian diperluas ke setup ICT yang belum tercakup di ronde 1.)*

Setup yang diuji di ronde ini: **BOS/CHoCH, Turtle Soup, OTE (Optimal Trade Entry), Premium/Discount, Power of 3 (AMD)**. Semua kausal — swing dikonfirmasi dengan `shift(n)`, tidak ada `shift` negatif.

## A. Hasil Mentah

### Timeframe M15 — semua gagal

| Setup | n | h48 gross | **h48 net** |
|---|---|---|---|
| BOS bullish → long | 16,225 | +3.02 | **−0.58** |
| BOS bearish → short | 15,795 | −1.49 | **−5.09** |
| Turtle Soup low → long | 19,464 | +2.06 | **−1.54** |
| Turtle Soup high → short | 19,512 | −3.07 | **−6.67** |
| OTE long | 9,088 | −0.35 | **−3.95** |
| OTE short | 9,022 | −3.22 | **−6.82** |
| Premium → short | 65,801 | −3.68 | **−7.28** |

Konsisten dengan ronde 1: di M15, biaya 3.6 bps menghapus semuanya.

### Timeframe H1 — beberapa terlihat positif

| Setup | n | h48 gross | **h48 net** | t |
|---|---|---|---|---|
| **OTE long** | 2,449 | +15.61 | **+12.01** | +5.1 |
| **Turtle Soup low → long** | 5,480 | +13.45 | **+9.85** | +6.6 |
| **BOS bullish → long** | 3,877 | +10.09 | **+6.49** | +4.2 |
| Discount → long | 15,730 | +5.34 | +1.74 | +4.5 |
| Turtle Soup high → short | 5,404 | −7.91 | **−11.51** | −3.7 |
| OTE short | 2,590 | −9.92 | **−13.52** | −3.4 |
| Premium → short | 17,908 | −8.66 | **−12.26** | −7.8 |

Di sini muncul pola mencolok: **setiap setup long positif, setiap setup short negatif.** Itu bukan tanda edge — itu tanda **bias arah**. Maka saya jalankan uji kontrol.

## B. Uji Kontrol — Benchmark yang Sebenarnya

Pertanyaan yang harus diajukan: apakah setup ini mengalahkan **long acak tanpa setup apa pun**?

```
long ACAK n=2,500, hold 48 jam : gross +8.34 bps   net +4.74   (t +2.65)
long ACAK n=5,500, hold 48 jam : gross +8.80 bps   net +5.20   (t +4.41)
long ACAK n=9,000, hold 48 jam : gross +7.55 bps   net +3.95   (t +4.80)
SEMUA bar (drift pasif)        : gross +9.84 bps   net +6.24
```

**Melempar dadu dan long emas menghasilkan +8.8 bps per 48 jam, net +5.20, dengan t-stat 4.41.**

Itulah benchmark sesungguhnya — bukan nol. Emas naik +230% dalam periode dataset ini; setiap strategi long-only akan terlihat profitable.

### Excess return setelah dikurangi drift

| Setup | Gross | Net | **Excess vs drift** | **t-stat excess** |
|---|---|---|---|---|
| OTE long | +15.61 | +12.01 | **+5.77** | **+1.88** |
| Turtle Soup low → long | +13.45 | +9.85 | **+3.62** | **+1.77** |
| BOS bullish → long | +10.09 | +6.49 | **+0.25** | **+0.11** |
| Discount zone → long | +5.34 | +1.74 | **−4.49** | **−3.77** ❌ |

Angka "t = +5.1" pada OTE runtuh menjadi **t = +1.88** setelah drift dikeluarkan — di bawah ambang signifikansi (t > 2). BOS runtuh menjadi **t = +0.11**, praktis nol.

**Discount zone justru secara signifikan LEBIH BURUK dari long acak** (t = −3.77). Menunggu harga masuk zona diskon berarti melewatkan tren — Anda membeli kelemahan di aset yang sedang naik.

### Uji per tahun — Turtle Soup (setup terbaik) vs drift pasif

| Tahun | Setup | Drift pasif | Excess | Menang? |
|---|---|---|---|---|
| 2016 | −25.30 | −30.46 | +5.16 | ✅ |
| 2017 | +18.74 | +10.13 | +8.61 | ✅ |
| 2018 | −5.52 | −1.62 | −3.90 | ❌ |
| 2019 | +14.28 | +14.29 | −0.01 | ❌ |
| 2020 | +27.05 | +18.91 | +8.14 | ✅ |
| 2021 | +4.68 | −5.48 | +10.16 | ✅ |
| 2022 | +12.97 | +1.47 | +11.50 | ✅ |
| 2023 | +7.58 | +8.91 | −1.33 | ❌ |
| 2024 | +21.11 | +20.33 | +0.78 | ✅ |
| 2025 | +38.48 | +41.12 | −2.64 | ❌ |
| 2026 | +4.66 | +0.54 | +4.12 | ✅ |

**7 dari 11 tahun.** Melempar koin menghasilkan 5.5. Dengan n=11, hasil 7/11 punya p-value ≈ 0.27 — **tidak signifikan**.

## C. Power of 3 / AMD — Gagal

| Setup | n | Gross | Net | t | Tahun positif |
|---|---|---|---|---|---|
| Sweep LOW Asia pagi → long siang | 894 | **−4.73** | −8.33 | −1.79 | 3/11 |
| Sweep HIGH Asia pagi → short siang | 1,004 | +0.08 | −3.52 | +0.04 | 5/11 |

Konsisten dengan temuan Judas Swing di ronde 1: **model manipulasi-lalu-reversal tidak terjadi pada XAUUSD.**

## D. Kesimpulan Ronde 2

Tiga lapis penyaringan, dan setiap lapis menggugurkan lebih banyak:

| Lapis uji | Yang lolos |
|---|---|
| 1. Gross return positif | OTE, Turtle Soup, BOS, Discount (H1) |
| 2. Setelah biaya 3.6 bps | OTE, Turtle Soup, BOS |
| 3. **Setelah dikurangi drift emas** | **Tidak ada** (t maks = 1.88, di bawah ambang) |

**Tidak ada setup ICT/SMC yang terbukti menambah nilai di atas sekadar "long emas secara acak dan tahan 2 hari".**

Yang terjadi pada backtest H1 di bagian A adalah **setup long menangkap drift struktural emas**, bukan menemukan edge. Buktinya: sisi short — yang melawan drift — rugi besar di **semua** setup tanpa kecuali (−11.51, −12.26, −13.52). Kalau ICT benar-benar membaca "jejak smart money", sisi short seharusnya juga bekerja.

**Nuansa yang adil:** OTE dan Turtle Soup punya excess t-stat 1.8–1.9. Itu bukan nol — arahnya benar, dan dengan data lebih panjang mungkin mencapai signifikansi. Tapi 1.88 adalah wilayah "mungkin ada sesuatu yang sangat tipis", bukan dasar untuk mempertaruhkan modal, apalagi setelah saya menguji puluhan varian (multiple-testing: dengan ~30 setup diuji, satu-dua akan mencapai t≈2 murni karena kebetulan).

**Implikasi praktis:** kalau Anda trading ICT long-only di XAUUSD 2016–2026 dan profit, hasil itu kemungkinan besar berasal dari **emas yang naik 230%**, bukan dari setup-nya. Cara mengujinya: bandingkan hasil Anda dengan sekadar buy & hold di periode yang sama. Itu benchmark yang jujur.

