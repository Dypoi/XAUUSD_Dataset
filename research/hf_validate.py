exec(open('hf_search2.py').read().split('print("="*128)')[0])
BEST=mk(bsl_swept&bull_disp&bias)
CFG=dict(conc=8,ts=288,risk=20.0)
r=run(BEST,**CFG)
print("="*112); print("KANDIDAT: sweep BSL + displacement + bias H4-240 | 8 posisi paralel | time-stop 24 jam | risk $20/posisi")
print("="*112)
print(f"n={r['n']:,}  /hari={r['perday']:.2f}  WR={r['wr']:.2f}%  PF={r['pf']:.3f}  final=${r['final']:,.0f}  DD={r['dd']:.2f}%  CAGR={r['cagr']:.2f}%  t={r['t']:+.2f}")

print()
print("="*112); print("A. UJI KONTROL — entry ACAK, jumlah & geometri & aturan risiko IDENTIK"); print("="*112)
rng=np.random.default_rng(21); nsig=int((BEST!=0).sum()); pfs=[];fins=[]
for k in range(8):
    rs=np.zeros(len(BEST),np.int64); rs[rng.choice(len(BEST)-10,nsig,replace=False)]=1
    rr_=run(rs,**CFG); pfs.append(rr_['pf']); fins.append(rr_['final'])
    if k<3: print(f"  ACAK #{k+1}: PF={rr_['pf']:.3f} WR={rr_['wr']:.2f}% final=${rr_['final']:,.0f} DD={rr_['dd']:.1f}%")
print(f"  ACAK rata2 8 seed: PF={np.mean(pfs):.3f} final=${np.mean(fins):,.0f}")
print(f"  KANDIDAT         : PF={r['pf']:.3f} final=${r['final']:,.0f}")
print(f"  >>> SELISIH      : PF {r['pf']-np.mean(pfs):+.3f}  ${r['final']-np.mean(fins):+,.0f}")

print()
print("="*112); print("B. IN-SAMPLE / OUT-OF-SAMPLE"); print("="*112)
for lbl,mask in (("IS  2016-09..2021-08",m5.index<'2021-09-01'),("OOS 2021-09..2026-09",m5.index>='2021-09-01')):
    s=BEST.copy(); s[~mask]=0
    x=run(s,**CFG)
    print(f"{lbl}: n={x['n']:5d} /hari={x['perday']*2:.2f} WR={x['wr']:6.2f}% PF={x['pf']:6.3f} final=${x['final']:9,.0f} DD={x['dd']:7.2f}% t={x['t']:+5.2f}")

print()
print("="*112); print("C. STRESS BIAYA"); print("="*112)
for extra,lbl in ((0,"Baseline (spread dataset ~3.4p)"),(0.10,"+1 pip"),(0.20,"+2 pips"),(0.30,"+3 pips"),(0.50,"+5 pips (total ~8.4p)")):
    x=run(BEST,slip=0.02+extra,**CFG)
    print(f"{lbl:34s} PF={x['pf']:6.3f} final=${x['final']:9,.0f} DD={x['dd']:7.2f}%")

print()
print("="*112); print("D. SENSITIVITAS SL / RR / TIME-STOP"); print("="*112)
print(f"{'SL$':>5s} {'RR':>5s} {'TS(bar)':>8s} {'n':>6s} {'/hari':>6s} {'PF':>7s} {'Final$':>10s} {'DD%':>7s}")
for sl in (10.0,12.0,15.0):
    for rrx in (1.5,2.0,3.0):
        x=run(BEST,sl=sl,rr=rrx,**CFG)
        print(f"{sl:5.0f} 1:{rrx:<3.1f} {288:8d} {x['n']:6d} {x['perday']:6.2f} {x['pf']:7.3f} {x['final']:10,.0f} {x['dd']:7.2f}")

print()
print("="*112); print("E. PER TAHUN"); print("="*112)
tr=r['tr']
yr=tr.groupby(tr.index.year)['usd'].agg(['count','sum'])
yr['PF']=tr.groupby(tr.index.year)['usd'].apply(lambda x:x[x>0].sum()/max(-x[x<0].sum(),1e-9))
yr['WR%']=tr.groupby(tr.index.year)['usd'].apply(lambda x:(x>0).mean()*100)
yr['/hari']=yr['count']/252
yr['eq']=tr.groupby(tr.index.year)['eq'].last()
print(yr.round(2).to_string())
r['tr'].to_parquet('/home/user/XAUUSD_Dataset/reports/hf_trades.parquet')
import pickle; pickle.dump(r,open('/tmp/hfbest.pkl','wb'))
