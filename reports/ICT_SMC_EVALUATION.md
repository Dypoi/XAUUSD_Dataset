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
