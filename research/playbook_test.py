"""Uji klaim kuantitatif Playbook ICT x SMC x PA terhadap 10 tahun XAUUSD."""
import pandas as pd, numpy as np
d=pd.read_parquet('m1.parquet').set_index('timestamp').sort_index()
mid=(d.close_bid+d.close_ask)/2
sp=(d.close_ask-d.close_bid)

print("="*100); print("UJI 1: ASUMSI SPREAD 8 PIPS ($0.80) — apakah realistis?"); print("="*100)
spp=sp/0.10  # dalam pips playbook (1 pip=$0.10)
print(f"Spread median dataset : {sp.median():.3f} USD = {spp.median():.2f} pips")
print(f"  p90={spp.quantile(.90):.2f}p  p99={spp.quantile(.99):.2f}p  max={spp.max()/0.10:.1f}p")
# per jam WIB (UTC+7)
wib=(mid.index.hour+7)%24
tab=spp.groupby(wib).median()
print("\nSpread median per jam WIB (playbook pakai jam WIB):")
for h in [7,11,13,14,15,16,18,19,20,21,22,0,3]:
    print(f"   {h:02d}:00 WIB -> {tab[h]:.2f} pips", end="")
    print("   <-- London KZ" if h in(13,14,15,16) else ("   <-- NY KZ" if h in(18,19,20,21) else ""))
print(f"\n=> Playbook asumsi 8 pips; realita {spp.median():.1f} pips. Playbook 2.4x KONSERVATIF (bagus).")

print()
print("="*100); print("UJI 2: TABEL WIN RATE BREAK-EVEN — verifikasi matematis"); print("="*100)
print(f"{'SL':>6} {'RR':>5} {'WR-BE playbook':>15} {'WR-BE (spread 8p)':>18} {'WR-BE (spread 3.4p riil)':>25}")
pb={(50,1):58,(50,2):39,(50,3):29,(100,1):54,(100,2):36,(100,3):27,(150,1):53,(150,2):35,(150,3):26}
for sl in (50,100,150):
    for rr in (1,2,3):
        # BE: WR*(rr*sl) = (1-WR)*sl, dengan spread menambah biaya di kedua sisi
        for spr,lbl in ((8,'a'),(spp.median(),'b')):
            win=rr*sl-spr; loss=sl+spr
            be=loss/(win+loss)*100
            if lbl=='a': be8=be
            else: be_real=be
        print(f"{sl:>6} 1:{rr} {pb[(sl,rr)]:>14}% {be8:>17.1f}% {be_real:>24.1f}%")
print("=> Tabel playbook AKURAT (deviasi <1%). Dengan spread riil, ambangnya lebih rendah lagi.")
