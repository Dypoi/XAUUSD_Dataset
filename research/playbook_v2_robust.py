src=open('playbook_v2.py').read().split('print("='+'"*126)')[0].replace('@njit(cache=True)','@njit')
exec(src)
BEST=mksig(v2_buy,pd.Series(False,index=m5.index))
mask_is=(m5.index<'2021-09-01'); mask_oos=~mask_is

print("="*110); print("A. SPLIT IN-SAMPLE / OUT-OF-SAMPLE"); print("="*110)
for lbl,mk in (("IS  2016-09..2021-08",mask_is),("OOS 2021-09..2026-09",mask_oos)):
    s=BEST.copy(); s[~mk]=0
    r=run(s)
    print(f"{lbl}: n={r['n']:5d} WR={r['wr']:6.2f}% PF={r['pf']:6.3f} net=${r['net']:+8,.0f} "
          f"final=${r['final']:8,.0f} DD={r['dd']:6.2f}% t={r['tr'].usd.mean()/(r['tr'].usd.std()/np.sqrt(r['n'])):+5.2f}")

print()
print("="*110); print("B. SENSITIVITAS SL & RR"); print("="*110)
print(f"{'SL($)':>7s} {'RR':>5s} {'n':>6s} {'WR%':>7s} {'PF':>7s} {'Final$':>10s} {'DD%':>7s}")
for sl in (8.0,10.0,12.0,15.0,20.0):
    for rr in (1.5,2.0,3.0):
        r=run(BEST,sl_usd=sl,rr=rr)
        print(f"{sl:7.0f} 1:{rr:<4.1f} {r['n']:6d} {r['wr']:7.2f} {r['pf']:7.3f} {r['final']:10,.0f} {r['dd']:7.2f}")

print()
print("="*110); print("C. SENSITIVITAS ATURAN RISIKO PLAYBOOK"); print("="*110)
print(f"{'Konfigurasi':44s} {'n':>6s} {'PF':>7s} {'Final$':>10s} {'DD%':>7s} {'entry/hari':>11s}")
for lbl,kw in (("Baseline: 2/hari, stop $250/$400, 2 loss",dict()),
               ("3 trade/hari (versi hal.6)",dict(maxday=3)),
               ("Tanpa batas trade harian",dict(maxday=99)),
               ("Tanpa stop rugi/profit harian",dict(dl=1e9,dp=1e9)),
               ("Tanpa circuit breaker 2-loss",dict(mcl=99)),
               ("TANPA SEMUA GUARDRAIL",dict(maxday=99,dl=1e9,dp=1e9,mcl=99)),
               ("Risk $50 (0.5%)",dict(risk=50.0)),
               ("Risk $160 (1.6%)",dict(risk=160.0)),
               ("Risk $500 (5% ala bot ICAS)",dict(risk=500.0))):
    r=run(BEST,**kw)
    print(f"{lbl:44s} {r['n']:6d} {r['pf']:7.3f} {r['final']:10,.0f} {r['dd']:7.2f} {r['n']/(10*252):11.2f}")

print()
print("="*110); print("D. STRESS BIAYA (spread tambahan per sisi)"); print("="*110)
print(f"{'Skenario':30s} {'PF':>7s} {'Final$':>10s} {'DD%':>7s}")
for extra,lbl in ((0.0,"Baseline (spread dataset)"),(0.10,"+1 pip"),(0.20,"+2 pips"),
                  (0.30,"+3 pips"),(0.50,"+5 pips (broker buruk)")):
    r=run(BEST,slip=0.02+extra)
    print(f"{lbl:30s} {r['pf']:7.3f} {r['final']:10,.0f} {r['dd']:7.2f}")
