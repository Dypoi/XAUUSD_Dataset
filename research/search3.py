import pandas as pd,numpy as np,lab
b=lab.make('4h'); BPY=6*252
c=np.log(b.c); vol=b.ret.rolling(500).std()
def z(n): return (c-c.shift(n))/(vol*np.sqrt(n))
ens=(np.tanh(z(120))+np.tanh(z(240))+np.tanh(z(720)))/3
variants={
 'LS ens':ens,
 'LS ens sm6':ens.rolling(6).mean(),
 'LongOnly ens':ens.clip(0,None),
 'LongOnly ens sm6':ens.rolling(6).mean().clip(0,None),
 'LongBias 0.5+0.5ens':0.5+0.5*ens,
 'BuyHold':pd.Series(1.0,index=b.index),
}
rows=[]
for name,p in variants.items():
    for vt in (0.10,0.15,0.20):
        r=lab.evaluate(b,p.fillna(0),BPY,vol_target=vt,cap=3,name=f"{name} vt{vt}")
        rows.append({k:v for k,v in r.items() if k not in('net','eq','expo')})
df=pd.DataFrame(rows)
print(df.round(3).to_string(index=False))
