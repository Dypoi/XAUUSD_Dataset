"""APAKAH STRATEGI INI MEMPREDIKSI MARKET STRUCTURE? Uji jujur."""
exec(open('hf_search2.py').read().split('print("="*128)')[0])
SIG=(bsl_swept&bull_disp&bias).fillna(False)
lg=np.log(m5.c)

# definisi struktur: swing 5-bar terkonfirmasi
n=5
swh=(m5.h==m5.h.rolling(2*n+1,center=True).max()).shift(n).fillna(False)
swl=(m5.l==m5.l.rolling(2*n+1,center=True).min()).shift(n).fillna(False)
last_h=m5.h.where(swh).ffill(); last_l=m5.l.where(swl).ffill()

print("="*112)
print("UJI 1: Apakah sinyal memprediksi BOS (Break of Structure) berikutnya?")
print("="*112)
# BOS ke atas = harga tembus last swing high; BOS bawah = tembus last swing low
fwd_up=pd.Series(False,index=m5.index); fwd_dn=pd.Series(False,index=m5.index)
H=288  # 24 jam ke depan
fut_max=m5.h.shift(-H).rolling(H).max().shift(-0)  # perkiraan
fut_max=m5.h[::-1].rolling(H,min_periods=1).max()[::-1].shift(-1)
fut_min=m5.l[::-1].rolling(H,min_periods=1).min()[::-1].shift(-1)
bos_up=(fut_max>last_h); bos_dn=(fut_min<last_l)
both=bos_up&bos_dn; only_up=bos_up&~bos_dn; only_dn=bos_dn&~bos_up
for lbl,m_ in (("SAAT ADA SINYAL",SIG),("SEMUA BAR (baseline)",pd.Series(True,index=m5.index))):
    mm=m_.fillna(False)
    print(f"{lbl:24s}: BOS-naik saja={only_up[mm].mean()*100:5.1f}%  BOS-turun saja={only_dn[mm].mean()*100:5.1f}%  "
          f"dua-duanya={both[mm].mean()*100:5.1f}%  rasio naik/turun={only_up[mm].mean()/max(only_dn[mm].mean(),1e-9):.3f}")

print()
print("="*112)
print("UJI 2: Berapa lag bias H4-MA240? (seberapa TERLAMBAT filternya)")
print("="*112)
h4c=m5.c.resample('4h').last().dropna()
b=(h4c>h4c.rolling(240).mean())
flip=b.ne(b.shift())
turns=b.index[flip & b.notna()]
# bandingkan titik balik bias dgn titik balik harga aktual (swing H4 60-bar)
ph=(h4c==h4c.rolling(121,center=True).max()); pl=(h4c==h4c.rolling(121,center=True).min())
piv=h4c.index[(ph|pl).fillna(False)]
lags=[]
for t in turns:
    prev=piv[piv<=t]
    if len(prev): lags.append((t-prev[-1]).total_seconds()/3600/24)
lags=np.array(lags)
print(f"Jumlah pergantian bias : {len(turns)}")
print(f"LAG rata-rata dari titik balik harga : {np.mean(lags):.1f} hari (median {np.median(lags):.1f})")
print(f"=> Filter bias TERTINGGAL rata-rata {np.mean(lags):.0f} hari. Ini REAKTIF, bukan prediktif.")

print()
print("="*112)
print("UJI 3: Nilai prediktif sinyal — distribusi arah 24 jam ke depan")
print("="*112)
f=(lg.shift(-288)-lg)*1e4
x=f[SIG].dropna(); base=f.dropna()
print(f"Saat ada sinyal : naik={100*(x>0).mean():.2f}%  mean={x.mean():+.2f}bps  median={x.median():+.2f}")
print(f"Baseline semua  : naik={100*(base>0).mean():.2f}%  mean={base.mean():+.2f}bps  median={base.median():+.2f}")
print(f"EDGE prediktif  : {100*(x>0).mean()-100*(base>0).mean():+.2f} poin persen arah")
print(f"                  {x.mean()-base.mean():+.2f} bps excess")
print()
print("KESIMPULAN: sinyal HANYA menggeser probabilitas beberapa poin persen.")
print("Itu BUKAN prediksi struktur — itu edge statistik tipis yang butuh ratusan trade.")
