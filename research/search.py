import pandas as pd,numpy as np,lab
b1=lab.make('1h'); BPY1=24*252
b4=lab.make('4h'); BPY4=6*252
rows=[]
for b,bpy,tag in ((b1,BPY1,'1h'),(b4,BPY4,'4h')):
    c=np.log(b.c); vol=b.ret.rolling(500).std()
    for n in (6,12,24,48,96,168,336,720):
        sig=(c-c.shift(n))/(vol*np.sqrt(n))
        for mode,pos in (('cont',np.tanh(sig)),('rev',-np.tanh(sig))):
            r=lab.evaluate(b,pos.fillna(0),bpy,name=f"{tag} mom{n} {mode}")
            rows.append(r)
df=pd.DataFrame([{k:v for k,v in r.items() if k not in ('net','eq','expo')} for r in rows])
print(df.sort_values('sharpe',ascending=False).head(15).round(3).to_string(index=False))
