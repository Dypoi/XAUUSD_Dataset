import pandas as pd, numpy as np
d=pd.read_parquet('m1.parquet').set_index('timestamp').sort_index()
mid=(d.close_bid+d.close_ask)/2
m5=pd.DataFrame({'o':mid.resample('5min').first(),'h':mid.resample('5min').max(),
 'l':mid.resample('5min').min(),'c':mid.resample('5min').last()}).dropna()
COST=3.6  # bps round-turn

print("="*112)
print("UJI 3: 'JANGAN KEJAR DORONGAN PERTAMA, TUNGGU BALIKANNYA' (Judas Swing, Anatomi hal.15)")
print("="*112)
# Fase manipulasi London (13-16 WIB = 06-09 UTC): arah dorongan pertama vs arah sisa hari
h=m5.index.hour; day=m5.index.normalize()
lon=(h>=6)&(h<9)
lon_o=m5.o.where(lon).groupby(day).first(); lon_c=m5.c.where(lon).groupby(day).last()
first_push=np.sign(lon_c-lon_o)             # arah dorongan London
# sisa hari: 09-20 UTC (NY distribusi)
ny=(h>=9)&(h<20)
ny_o=m5.o.where(ny).groupby(day).first(); ny_c=m5.c.where(ny).groupby(day).last()
ny_ret=(np.log(ny_c)-np.log(ny_o))*1e4
df=pd.DataFrame({'push':first_push,'ny':ny_ret}).dropna()
for p,lbl in ((1,'London dorong NAIK'),(-1,'London dorong TURUN')):
    x=df[df.push==p].ny
    print(f"{lbl}: n={len(x):4d} | NY lanjut searah = {x.mean()*p:+6.2f}bps | NY BALIK arah = {-x.mean()*p:+6.2f}bps  (t={x.mean()/(x.std()/np.sqrt(len(x))):+5.2f})")
fade=(-df.push*df.ny); cont=(df.push*df.ny)
print(f"\nSTRATEGI FADE dorongan London : mean={fade.mean():+6.2f}bps net={fade.mean()-COST:+6.2f} t={fade.mean()/(fade.std()/np.sqrt(len(fade))):+5.2f}")
print(f"STRATEGI IKUT dorongan London : mean={cont.mean():+6.2f}bps net={cont.mean()-COST:+6.2f} t={cont.mean()/(cont.std()/np.sqrt(len(cont))):+5.2f}")
yr=fade.groupby(fade.index.year).mean()
print(f"Fade: tahun positif {int((yr>0).sum())}/{len(yr)}")

print()
print("="*112)
print("UJI 4: 'CARA HARGA MASUK ZONA' — retracement pelan vs displacement (Anatomi hal.8)")
print("="*112)
# definisi: level = swing low 5-bar terkonfirmasi. Cara datang = kecepatan 6 bar terakhir sblm sentuh
n=5
sl_=(m5.l==m5.l.rolling(2*n+1,center=True).min()).shift(n).fillna(False)
lvl=m5.l.where(sl_).ffill()
atr=(m5.h-m5.l).rolling(48).mean()
touch=(m5.l<=lvl)&(m5.l.shift(1)>lvl)&lvl.notna()
speed=(m5.c.shift(1)-m5.c.shift(7)).abs()/(atr*6)   # seberapa impulsif datangnya
lg=np.log(m5.c)
print(f"{'Cara datang ke zona demand':38s} {'n':>7s} {'h12':>9s} {'h24':>9s} {'h48':>9s}")
for lbl,cond in (("PELAN (retracement korektif)",speed<0.35),("SEDANG",(speed>=0.35)&(speed<0.8)),("MENGHUNJAM (displacement)",speed>=0.8)):
    m=(touch&cond).fillna(False)
    row=[f"{lbl:38s} {int(m.sum()):7d}"]
    for k in (12,24,48):
        f=(lg.shift(-k)-lg)*1e4
        x=f[m].dropna()
        row.append(f"{x.mean():+9.2f}")
    print(" ".join(row))
print("=> Klaim playbook: datang PELAN -> zona dihormati (return long positif);")
print("   datang MENGHUNJAM -> zona jebol (return long negatif/lemah).")

print()
print("="*112)
print("UJI 5: FREKUENSI — klaim '2-3 setup per minggu' vs bot ICAS lama")
print("="*112)
print(f"{'Sistem':46s} {'trade/minggu':>14s} {'trade/tahun':>13s}")
print(f"{'Playbook target (2-3/minggu)':46s} {'2 - 3':>14s} {'104 - 156':>13s}")
print(f"{'Bot ICAS lama (audit Anda, Jan-Jun 2026)':46s} {4.73*5:>14.1f} {4.73*252:>13.0f}")
print(f"{'Replikasi ICAS saya (10 thn)':46s} {0.40*5:>14.1f} {0.40*252:>13.0f}")
print(f"{'XAU-TRV (rebalance)':46s} {12/52:>14.2f} {12:>13d}")
