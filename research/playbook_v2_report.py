src=open('playbook_v2.py').read().split('print("='+'"*126)')[0].replace('@njit(cache=True)','@njit')
exec(src)

BEST=mksig(v2_buy,pd.Series(False,index=m5.index))   # V2 long-only
FULL=mksig(v2_buy,v2_sell)                            # V2 lengkap 2 arah
V1  =mksig(v1_buy,v1_sell)

def detail(r,label):
    tr=r['tr']; p=tr.usd.values
    ec=r['eqser']
    yrs=r['yrs']
    dd=(ec/ec.cummax()-1)
    # DD berbasis kalender harian
    eqd=ec.resample('D').last().ffill()
    ddd=(eqd/eqd.cummax()-1)
    ndays=r['active_days']
    print(f"\n{'='*104}\n{label}\n{'='*104}")
    print(f"Trades                 : {r['n']:,}  ({yrs:.1f} tahun)")
    print(f"Win rate               : {r['wr']:.2f}%")
    print(f"Profit Factor          : {r['pf']:.3f}")
    print(f"Net P/L                : ${r['net']:+,.0f}")
    print(f"Balance $10,000     -> : ${r['final']:,.0f}   ({(r['final']/10000-1)*100:+.1f}%)")
    print(f"CAGR                   : {r['cagr']:.2f}%/tahun")
    print(f"Max Drawdown           : {r['dd']:.2f}%  (harian: {ddd.min()*100:.2f}%)")
    print(f"Avg win / avg loss     : ${r['avg_win']:+.2f} / ${r['avg_loss']:+.2f}   payoff={abs(r['avg_win']/r['avg_loss']):.2f}")
    print(f"Expectancy per trade   : ${p.mean():+.2f}")
    print(f"t-stat                 : {p.mean()/(p.std()/np.sqrt(len(p))):+.2f}")
    print(f"ENTRY PER HARI         : {r['n']/(10*252):.2f} (rata2 semua hari bursa)")
    print(f"                         {r['n']/ndays:.2f} (pada hari yang ada trade)")
    print(f"Hari aktif             : {ndays:,} dari ~2,520 hari bursa ({ndays/2520*100:.0f}%)")
    print(f"Entry per minggu       : {r['n']/(yrs*52):.2f}")
    yr=tr.groupby(tr.index.year).usd.agg(['count','sum'])
    yr['PF']=tr.groupby(tr.index.year).usd.apply(lambda x:x[x>0].sum()/max(-x[x<0].sum(),1e-9))
    yr['WR%']=tr.groupby(tr.index.year).usd.apply(lambda x:(x>0).mean()*100)
    yr['eq_akhir']=tr.groupby(tr.index.year).eq.last()
    print("\nPer tahun:"); print(yr.round(2).to_string())
    return r

rB=run(BEST); rF=run(FULL); rV=run(V1)
detail(rB,"KONFIGURASI TERBAIK — V2 LONG-ONLY (fix1+2+3, SELL dimatikan total)")
detail(rF,"V2 LENGKAP 2 ARAH (SELL aktif hanya saat bias D/H4 bearish)")

print(f"\n{'='*104}\nPERBANDINGAN LANGSUNG\n{'='*104}")
print(f"{'':44s} {'PF':>7s} {'WR%':>7s} {'Final$':>10s} {'DD%':>8s} {'entry/hari':>11s}")
for nm,r in (("V1 playbook ASLI (tanpa perbaikan)",rV),("V2 lengkap 2 arah",rF),("V2 LONG-ONLY",rB)):
    print(f"{nm:44s} {r['pf']:7.3f} {r['wr']:7.2f} {r['final']:10,.0f} {r['dd']:8.1f} {r['n']/(10*252):11.2f}")

# ---------- KONTROL: acak dgn geometri & aturan risiko identik ----------
print(f"\n{'='*104}\nUJI KONTROL — entry ACAK, geometri + aturan risiko IDENTIK\n{'='*104}")
rng=np.random.default_rng(3); nsig=int((BEST!=0).sum()); pfs=[];fins=[]
for k in range(8):
    rs=np.zeros(len(BEST),np.int64)
    rs[rng.choice(len(BEST)-10,nsig,replace=False)]=1   # long-only acak
    rr_=run(rs)
    pfs.append(rr_['pf']); fins.append(rr_['final'])
    if k<3: print(f"  ACAK long-only #{k+1}: PF={rr_['pf']:.3f} WR={rr_['wr']:.2f}% final=${rr_['final']:,.0f} DD={rr_['dd']:.1f}%")
print(f"  ACAK rata-rata 8 seed : PF={np.mean(pfs):.3f}  final=${np.mean(fins):,.0f}")
print(f"\n  V2 LONG-ONLY          : PF={rB['pf']:.3f}  final=${rB['final']:,.0f}")
print(f"  SELISIH vs acak       : PF {rB['pf']-np.mean(pfs):+.3f}   ${rB['final']-np.mean(fins):+,.0f}")

# ---------- Buy&Hold pembanding ----------
tot=(m5.c.iloc[-1]/m5.c.iloc[0])
print(f"\n  Buy&Hold emas 10 thn  : {(tot-1)*100:+.1f}%  -> $10,000 jadi ${10000*tot:,.0f}")
import pickle; pickle.dump(rB['tr'],open('/tmp/best.pkl','wb'))
rB['tr'].to_parquet('/home/user/XAUUSD_Dataset/reports/playbook_v2_trades.parquet')
