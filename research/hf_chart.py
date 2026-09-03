exec(open('hf_search2.py').read().split('print("="*128)')[0])
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
BEST=mk(bsl_swept&bull_disp&bias)
rHF=run(BEST,conc=8,ts=288,risk=20.0)
rHF30=run(BEST,conc=8,ts=288,risk=30.0)
# pembanding: V2 low-freq (1 posisi)
rLF=run(BEST,conc=1,ts=288,risk=80.0)
fig,ax=plt.subplots(2,1,figsize=(13,9),gridspec_kw={'height_ratios':[2,1]})
for r_,lbl,c in ((rLF,f"V2 lama: 0.52 entry/hari (PF {rLF['pf']:.2f})",'steelblue'),
                 (rHF,f"HF risk $20: 2.54 entry/hari (PF {rHF['pf']:.2f}) DD {rHF['dd']:.1f}%",'seagreen'),
                 (rHF30,f"HF risk $30: 2.54 entry/hari (PF {rHF30['pf']:.2f}) DD {rHF30['dd']:.1f}%",'darkorange')):
    ax[0].plot(r_['ec'].index,r_['ec'].values,label=lbl,lw=1.4,color=c)
ax[0].axhline(10000,ls='--',c='grey',lw=1)
ax[0].set_title('Strategi Frekuensi Tinggi — 2.54 entry/hari\nSweep BSL + displacement + bias H4 | 8 posisi paralel | time-stop 24 jam | net spread+slippage',fontsize=11)
ax[0].set_ylabel('Equity ($)'); ax[0].legend(loc='upper left'); ax[0].grid(alpha=.3)
e=rHF['ec']; dd=(e/e.cummax()-1)*100
ax[1].fill_between(e.index,dd.values,0,color='seagreen',alpha=.5)
ax[1].set_title('Drawdown (risk $20/posisi)'); ax[1].grid(alpha=.3); ax[1].set_ylabel('DD %')
plt.tight_layout(); plt.savefig('/home/user/XAUUSD_Dataset/reports/hf_equity.png',dpi=110)
print("HF20:",round(rHF['final']),"HF30:",round(rHF30['final']),"LF:",round(rLF['final']))
# distribusi jumlah entry harian
tr=rHF['tr']; cnt=tr.groupby(tr.index.normalize()).size()
print("distribusi entry/hari:",cnt.describe([.25,.5,.75,.9]).round(2).to_dict())
print("hari aktif:",len(cnt),"dari ~2520")
