"""Bongkar UJI 1: apakah rasio 21.5x itu prediksi, atau tautologi?"""
exec(open('hf_search2.py').read().split('print("="*128)')[0])
SIG=(bsl_swept&bull_disp&bias).fillna(False)
n=5
swh=(m5.h==m5.h.rolling(2*n+1,center=True).max()).shift(n).fillna(False)
swl=(m5.l==m5.l.rolling(2*n+1,center=True).min()).shift(n).fillna(False)
last_h=m5.h.where(swh).ffill(); last_l=m5.l.where(swl).ffill()
H=288
fut_max=m5.h[::-1].rolling(H,min_periods=1).max()[::-1].shift(-1)
fut_min=m5.l[::-1].rolling(H,min_periods=1).min()[::-1].shift(-1)
print("="*112)
print("BONGKAR UJI 1 — kenapa rasio 21.5x itu MENYESATKAN")
print("="*112)
dist_h=((last_h-m5.c)/m5.c*1e4)   # jarak ke swing high (bps)
dist_l=((m5.c-last_l)/m5.c*1e4)   # jarak ke swing low
print(f"{'Kondisi':28s} {'jarak ke swing HIGH':>22s} {'jarak ke swing LOW':>21s}")
print(f"{'Saat ada sinyal':28s} {dist_h[SIG].median():>19.1f}bps {dist_l[SIG].median():>18.1f}bps")
print(f"{'Baseline semua bar':28s} {dist_h.median():>19.1f}bps {dist_l.median():>18.1f}bps")
print()
print("=> Saat sinyal muncul, harga SUDAH nyaris menyentuh swing high (sweep BSL).")
print("   Jadi 'BOS naik' hampir pasti terjadi — itu BUKAN prediksi, itu DEFINISI setup.")
print()
print("UJI YANG BENAR: kontrol jarak. Bandingkan sinyal vs bar lain yang sama-sama dekat swing high.")
thr=dist_h[SIG].quantile(0.75)
near=(dist_h<=thr)
bos_up=(fut_max>last_h); bos_dn=(fut_min<last_l)
only_up=bos_up&~bos_dn; only_dn=bos_dn&~bos_up
for lbl,m_ in (("Sinyal (sweep+disp+bias)",SIG),("Kontrol: dekat high SAJA",near&~SIG)):
    mm=m_.fillna(False)
    r=only_up[mm].mean()/max(only_dn[mm].mean(),1e-9)
    print(f"  {lbl:30s} n={int(mm.sum()):7d}  BOS-naik={only_up[mm].mean()*100:5.1f}%  BOS-turun={only_dn[mm].mean()*100:5.1f}%  rasio={r:6.2f}")
print()
print("Kalau rasio sinyal ~= rasio kontrol, maka 'prediksi struktur'-nya berasal dari POSISI harga,")
print("bukan dari kecerdasan sinyal.")
