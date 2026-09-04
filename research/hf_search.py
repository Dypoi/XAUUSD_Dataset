"""Cari setup FREKUENSI TINGGI (>=2 entry/hari) yang tetap profitable net cost."""
src=open('playbook_v2.py').read().split('print("='+'"*126)')[0].replace('@njit(cache=True)','@njit')
exec(src)

lg=np.log(m5.c); atr=(m5.h-m5.l).rolling(48).mean()
vol=lg.diff().rolling(288).std()
h4=m5.c.resample('4h').last().dropna()
bias=(h4>h4.rolling(240).mean()).reindex(m5.index,method='ffill').fillna(False)
bias100=(h4>h4.rolling(100).mean()).reindex(m5.index,method='ffill').fillna(False)
m15c=m5.c.resample('15min').last().dropna()
bias_m15=(m15c>m15c.rolling(96).mean()).reindex(m5.index,method='ffill').fillna(False)

TARGET=2*252*10  # 5040 trades minimal utk 2/hari
cands={}

# --- A. Pullback ke MA dalam uptrend (frekuensi tinggi alami) ---
for ma_n in (24,48,96):
    ma=m5.c.rolling(ma_n).mean()
    for k in (0.5,1.0):
        sig=(m5.l<=ma-k*atr)&(m5.c>m5.o)&bias
        cands[f"A_pullbackMA{ma_n}_{k}atr"]=sig

# --- B. RSI-like oversold bounce dalam uptrend ---
delta=m5.c.diff()
up=delta.clip(lower=0).rolling(14).mean(); dn=(-delta.clip(upper=0)).rolling(14).mean()
rsi=100-100/(1+up/dn.replace(0,np.nan))
for th in (25,30,35):
    cands[f"B_rsi{th}_bias"]=(rsi<th)&(rsi.shift(1)>=th)&bias

# --- C. Breakout N-bar high dalam uptrend ---
for n in (12,24,48):
    hi=m5.h.rolling(n).max().shift(1)
    cands[f"C_break{n}_bias"]=(m5.c>hi)&bias

# --- D. FVG fill dalam uptrend ---
bfvg2=m5.l>(m5.h.shift(2)+0.10)
fvg_lvl=m5.h.shift(2).where(bfvg2).ffill(limit=60)
cands["D_fvgfill_bias"]=(m5.l<=fvg_lvl)&(m5.l.shift(1)>fvg_lvl)&fvg_lvl.notna()&bias

# --- E. Sweep swing low + continuation (versi v2 tapi longgar) ---
n=5
swl=(m5.l==m5.l.rolling(2*n+1,center=True).min()).shift(n).fillna(False)
lastswl=m5.l.where(swl).ffill()
cands["E_sweepswinglow_bias"]=(m5.l<lastswl)&(m5.c>lastswl)&(m5.c>m5.o)&bias

# --- F. v2 asli tapi bias longgar (M15/H4-100) ---
cands["F_v2_bias_m15"]=(bsl_swept&bull_disp&bias_m15)
cands["F_v2_bias_h4_100"]=(bsl_swept&bull_disp&bias100)
cands["F_v2_nobias"]=(bsl_swept&bull_disp)

# --- G. Momentum ignition: displacement bar dalam uptrend ---
disp=(m5.c-m5.o)>0.8*atr
cands["G_displacement_bias"]=disp&bias
cands["G_displacement_nobias"]=disp

print("="*122)
print(f"{'Setup':34s} {'sinyal':>8s} {'trades':>7s} {'/hari':>6s} {'WR%':>6s} {'PF':>7s} {'Final$':>10s} {'DD%':>7s} {'t':>6s}")
print("="*122)
rows=[]
for nm,sg in cands.items():
    s=mksig(sg,pd.Series(False,index=m5.index))
    nsig=int((s!=0).sum())
    r=run(s,sl_usd=12.0,rr=2.0,risk=80.0,maxday=99,dl=1e9,dp=1e9,mcl=99)
    if r is None or r['n']<50: continue
    perday=r['n']/(10*252)
    t=r['tr'].usd.mean()/(r['tr'].usd.std()/np.sqrt(r['n']))
    rows.append((nm,nsig,r['n'],perday,r['wr'],r['pf'],r['final'],r['dd'],t))
    print(f"{nm:34s} {nsig:8d} {r['n']:7d} {perday:6.2f} {r['wr']:6.2f} {r['pf']:7.3f} {r['final']:10,.0f} {r['dd']:7.1f} {t:+6.2f}")
print()
ok=[r for r in rows if r[3]>=2.0 and r[5]>1.0]
print(f"Memenuhi >=2 entry/hari DAN PF>1: {len(ok)}")
for r in sorted(ok,key=lambda x:-x[5]): print("  ",r[0],f"PF={r[5]:.3f} /hari={r[3]:.2f} final=${r[6]:,.0f}")
