import pandas as pd,numpy as np,lab
b=lab.make('5min'); BPY=288*252
c=b.c; lg=np.log(c)
ma=c.rolling(48).mean(); sd=c.rolling(48).std(); z=(c-ma)/sd
hour=b.index.hour
def run(z_th,hlo,hhi,hold,sides='both',stop=None):
    sess=(hour>=hlo)&(hour<hhi)
    s=pd.Series(0.0,index=b.index)
    if sides in('both','long'): s[(z<-z_th)&sess]=1
    if sides in('both','short'): s[(z>z_th)&sess]=-1
    pos=s.rolling(hold).mean()   # equal-weight overlapping entries
    return pos.fillna(0)
rows=[]
for zt in (2.0,2.5,3.0):
 for hold in (12,24,48):
  for sides in ('both','long','short'):
   pos=run(zt,0,7,hold,sides)
   r=lab.evaluate(b,pos,BPY,vol_target=0.10,cap=5,name=f"z{zt} hold{hold} {sides}")
   rows.append({k:v for k,v in r.items() if k not in('net','eq','expo')})
df=pd.DataFrame(rows)
print(df.sort_values('sharpe',ascending=False).round(3).to_string(index=False))
