src=open('playbook_v2.py').read().split('print("='+'"*126)')[0].replace('@njit(cache=True)','@njit')
exec(src)
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
BEST=mksig(v2_buy,pd.Series(False,index=m5.index)); FULL=mksig(v2_buy,v2_sell); V1=mksig(v1_buy,v1_sell)
rB=run(BEST); rF=run(FULL); rV=run(V1)
fig,ax=plt.subplots(2,1,figsize=(13,9),gridspec_kw={'height_ratios':[2,1]})
for r,lbl,c in ((rV,'V1 playbook ASLI (PF 0.86) — bangkrut','crimson'),
                (rF,'V2 lengkap 2 arah (PF 1.16)','darkorange'),
                (rB,'V2 LONG-ONLY (PF 1.28)','seagreen')):
    ax[0].plot(r['eqser'].index,r['eqser'].values,label=lbl,lw=1.5,color=c)
ax[0].axhline(10000,ls='--',c='grey',lw=1,label='Modal awal $10,000')
ax[0].set_title('Equity Curve — Playbook ICT×SMC×PA: sebelum vs sesudah 3 perbaikan\n($10,000 | risk $80/trade | maks 2 trade/hari | SL $12 | RR 1:2 | net spread+slippage)',fontsize=11)
ax[0].set_ylabel('Equity ($)'); ax[0].legend(loc='upper left'); ax[0].grid(alpha=.3)
e=rB['eqser']; dd=(e/e.cummax()-1)*100
ax[1].fill_between(e.index,dd.values,0,color='seagreen',alpha=.5)
ax[1].set_title('Drawdown V2 LONG-ONLY (%)'); ax[1].set_ylabel('DD %'); ax[1].grid(alpha=.3)
plt.tight_layout(); plt.savefig('/home/user/XAUUSD_Dataset/reports/playbook_v2_equity.png',dpi=110)
print("saved. final:",{k:round(v['final']) for k,v in (('V1',rV),('V2full',rF),('V2long',rB))})
