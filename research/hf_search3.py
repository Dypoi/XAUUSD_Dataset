exec(open('hf_search2.py').read().split('print("="*128)')[0])
print("="*130)
print("NORMALISASI RISIKO: risiko total portofolio dijaga konstan (risk/trade = $budget / max_conc)")
print("="*130)
print(f"{'Setup':30s} {'conc':>4s} {'TS':>4s} {'risk$':>6s} {'n':>6s} {'/hari':>6s} {'WR%':>6s} {'PF':>7s} {'Final$':>10s} {'DD%':>7s} {'t':>6s}")
print("-"*130)
sgs={'bias240':mk(bsl_swept&bull_disp&bias),'bias100':mk(bsl_swept&bull_disp&bias100)}
rows=[]
for nm,s in sgs.items():
    for conc in (3,5,8):
        for ts in (144,288):
            for budget in (80.0,160.0,240.0):
                rk=budget/conc
                r=run(s,conc=conc,ts=ts,risk=rk)
                if not r: continue
                rows.append((nm,conc,ts,rk,r))
                if r['perday']>=1.8:
                    print(f"{nm:30s} {conc:4d} {ts:4d} {rk:6.1f} {r['n']:6d} {r['perday']:6.2f} {r['wr']:6.2f} {r['pf']:7.3f} {r['final']:10,.0f} {r['dd']:7.1f} {r['t']:+6.2f}")
print()
ok=[x for x in rows if x[4]['perday']>=2.0 and x[4]['pf']>1.05 and x[4]['dd']>-25]
print(f"LOLOS: >=2/hari, PF>1.05, DD>-25% : {len(ok)}")
for nm,c,ts,rk,r in sorted(ok,key=lambda x:-x[4]['pf']):
    print(f"   {nm} conc{c} ts{ts} risk${rk:.0f}: PF={r['pf']:.3f} /hari={r['perday']:.2f} final=${r['final']:,.0f} DD={r['dd']:.1f}% CAGR={r['cagr']:.1f}%")
