import pandas as pd,numpy as np,lab,itertools
b=lab.make('4h'); BPY=6*252
c=np.log(b.c); vol=b.ret.rolling(500).std()
def z(n): return (c-c.shift(n))/(vol*np.sqrt(n))
rows=[]
for n1,n2,n3 in [(60,180,540),(90,240,720),(120,240,720),(120,360,1080),(180,540,1080)]:
    ens=(np.tanh(z(n1))+np.tanh(z(n2))+np.tanh(z(n3)))/3
    for th in (-0.6,-0.5,-0.35,-0.2,0.0):
        for floor in (0.0,0.25,0.4):
            pos=floor+(1-floor)*(ens>th).astype(float)
            r=lab.evaluate(b,pos.fillna(0),BPY,vol_target=0.10,cap=3)
            rf=lab.evaluate(b.loc[:'2021-08'],pos.loc[:'2021-08'].fillna(0),BPY,vol_target=0.10,cap=3)
            ro=lab.evaluate(b.loc['2021-09':],pos.loc['2021-09':].fillna(0),BPY,vol_target=0.10,cap=3)
            rows.append(dict(n=(n1,n2,n3),th=th,floor=floor,Sh=r['sharpe'],Cal=r['calmar'],
                             CAGR=r['cagr'],DD=r['maxdd'],ShIS=rf['sharpe'],ShOOS=ro['sharpe']))
df=pd.DataFrame(rows)
print(df.sort_values('Cal',ascending=False).head(20).round(3).to_string(index=False))
print("\nmedian Sharpe across grid:",df.Sh.median().round(3),"median Calmar:",df.Cal.median().round(3))
