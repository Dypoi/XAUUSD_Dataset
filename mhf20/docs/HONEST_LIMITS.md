# MHF-20 — Batas Jujur Sistem Ini

## Pertanyaan: "Apakah sudah bisa predict market structure?"

**Jawaban: TIDAK.** Bukti kuantitatif di bawah.

### Bukti 1 — Rasio BOS 21.5x itu TAUTOLOGI

| Kondisi | n | BOS naik | BOS turun | Rasio |
|---|---|---|---|---|
| Sinyal MHF-20 | 11.374 | 25,2% | 1,2% | **21,5x** |
| Kontrol: bar mana pun yang sama dekatnya ke swing high | 162.851 | 17,5% | 0,0% | **28.571x** |

Kontrol justru punya rasio LEBIH TINGGI. Sebabnya: saat sinyal muncul, jarak median
harga ke swing high sudah **−12,0 bps (sudah dilewati)**, sedangkan baseline +2,3 bps.
Setup ini *mensyaratkan* sweep BSL — jadi "break of structure ke atas" itu bagian dari
definisi entry, bukan ramalan.

### Bukti 2 — Filter bias H4 TERLAMBAT ~11 hari

394 pembalikan bias H4-MA240 vs pivot harga aktual:
**mean lag 10,6 hari · median 9,7 hari.** Filter ini reaktif; ia mengonfirmasi tren yang
sudah berjalan dua minggu, bukan memprediksi pergantiannya.

### Bukti 3 — Edge arah sebenarnya: 0,47 poin persen

| | Arah naik 24 jam | Return 24 jam |
|---|---|---|
| Saat sinyal | 53,73% | +7,41 bps |
| Baseline semua bar | 53,26% | +4,91 bps |
| **Selisih** | **+0,47 pp** | **+2,50 bps** |

## Kesimpulan

MHF-20 adalah **mesin kemiringan statistik**, bukan peramal struktur pasar. Ia:
- BEREAKSI pada sweep likuiditas yang sudah selesai
- MENYARING dengan tren yang sudah mapan (terlambat ~11 hari)
- MENGGESER peluang sekitar setengah poin persen per trade

Setengah poin persen itu nyata (t=+6,89, unggul +0,171 PF di atas entry acak) tapi hanya
terwujud lewat **ratusan sampai ribuan trade**. Pada 20 trade berikutnya hasilnya
praktis acak. Siapa pun yang memakai sistem ini harus paham: profitabilitas datang dari
repetisi dan disiplin risiko, bukan dari ketepatan membaca pasar.

## Risiko yang BELUM dimodelkan
1. **Swap/rollover** pada 8 posisi long paralel — bisa memakan 40–70% CAGR. Terbesar.
2. **Margin** — 8 posisi serentak butuh margin memadai di leverage 1:100.
3. **Korelasi** — 8 long XAUUSD bukan diversifikasi, itu satu taruhan berukuran 8x.
4. **Sampel bullish** — 2016–2026 emas naik +230%. Sistem long-only belum diuji di bear market panjang.
5. **Klasterisasi** — hanya 39% hari punya entry; pada hari aktif rata-rata 6,5 entry.
