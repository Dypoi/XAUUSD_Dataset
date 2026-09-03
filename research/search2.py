import pandas as pd,numpy as np,lab
b=lab.make('4h'); BPY=6*252
c=np.log(b.c); vol=b.ret.rolling(500).std()
def z(n): return (c-c.shift(n))/(vol*np.sqrt(n))
combos={
 'ens_120_240_720': (np.tanh(z(120))+np.tanh(z(240))+np.tanh(z(720)))/3,
 'ens_240_720_1080':(np.tanh(z(240))+np.tanh(z(720))+np.tanh(z(1080)))/3,
 'ens_all':(np.tanh(z(24))+np.tanh(z(120))+np.tanh(z(240))+np.tanh(z(720)))/4,
 'mom720':np.tanh(z(720)),
 'mom1080':np.tanh(z(1080)),
 'ens_24_720':(np.tanh(z(24))+np.tanh(z(720)))/2,
}
rows=[]
for name,s in combos.items():
    for smooth in (1,6,12,30):
        p=s.rolling(smooth).mean().fillna(0)
        for buf in (0,0.1,0.2):
            pp=p.where(p.diff().abs()>buf).ffill().fillna(0) if buf>0 else p
            r=lab.evaluate(b,pp,BPY,name=f"{name} sm{smooth} buf{buf}")
            rows.append({k:v for k,v in r.items() if k not in('net','eq','expo')})
df=pd.DataFrame(rows)
print(df.sort_values('sharpe',ascending=False).head(20).round(3).to_string(index=False))
