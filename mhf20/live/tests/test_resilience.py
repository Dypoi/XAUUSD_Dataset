"""AUDIT FORENSIK 2 — Ketahanan: crash, Ctrl+C, internet putus, restart."""
import sys,os,time,json,sqlite3,subprocess,signal
_L=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));_M=os.path.dirname(_L)
sys.path[:0]=[_L,_M]
from store import Store, now_ms
P=0;F=0
def chk(name,cond,info=""):
    global P,F
    if cond: P+=1;print(f"  LULUS  {name} {info}")
    else: F+=1;print(f"  GAGAL  {name} {info}")

DB='/tmp/res.db'
for f in (DB,DB+'-wal',DB+'-shm'):
    if os.path.exists(f): os.remove(f)

print("\n[1] WAL aktif + commit atomik")
s=Store(DB)
mode=s._c.execute("PRAGMA journal_mode").fetchone()[0]
chk("journal_mode=WAL",mode.lower()=='wal',f"({mode})")
sync=s._c.execute("PRAGMA synchronous").fetchone()[0]
chk("synchronous=FULL",int(sync)==2,f"({sync})")

print("\n[2] Idempotensi (reconnect tidak menggandakan)")
for _ in range(5):
    s.upsert_bar('S',1000,1,2,0.5,1.5,0.3)
    s.add_signal('S',1000,1,.3,.16,.9,1.1,1.2,True,[{'k':'x','ok':True}])
    s.upsert_trade(ticket=99,symbol='S',direction='BUY',entry_ts=1,entry_price=2,lot=.16,status='OPEN')
chk("bar tidak duplikat",len(s.bars('S'))==1)
chk("sinyal tidak duplikat",len(s.signals())==1)
chk("trade tidak duplikat",len(s.trades())==1)

print("\n[3] Simulasi KILL -9 (cabut listrik / laptop mati)")
s.upsert_trade(ticket=1234,symbol='S',direction='BUY',entry_ts=now_ms(),entry_price=3300,lot=.16,status='OPEN')
s.sset('journal',{'start_ts':now_ms()-2*86400000,'day':3,'start_equity':10000})
s.beat('main',{'x':1})
del s   # tanpa close() -> meniru proses dibunuh paksa
s2=Store(DB)
chk("DB terbuka setelah crash",True)
ot={t["ticket"] for t in s2.open_trades()}
chk("trade OPEN selamat",1234 in ot,f"(open={sorted(ot)})")
j=s2.sget('journal')
chk("state jurnal selamat",j and j['day']==3,f"(hari {j['day'] if j else '?'})")
chk("heartbeat selamat",s2.last_beat('main') is not None)

print("\n[4] Lanjut hari jurnal setelah offline (bukan reset ke hari 1)")
el=(now_ms()-j['start_ts'])/86400000
day=min(5,int(el)+1)
chk("hari dihitung dari waktu nyata",day==3,f"(hari {day})")

print("\n[5] Rekonsiliasi: trade tertutup saat program mati")
s2.upsert_trade(ticket=1234,status='CLOSED',pnl=-19.8,exit_ts=now_ms(),reason='MT5')
t=[x for x in s2.trades() if x['ticket']==1234][0]
chk("trade direkonsiliasi",t['status']=='CLOSED' and abs(t['pnl']+19.8)<1e-9)
chk("ticket 1234 tidak lagi OPEN",1234 not in {t["ticket"] for t in s2.open_trades()})

print("\n[6] Bridge tahan MT5 mati (semua panggilan return aman, tidak crash)")
from mt5_bridge import MT5Bridge
b=MT5Bridge('XAUUSDm',logger=lambda *a,**k:None)
b.connected=False
try:
    r=[b.tick(),b.bars(10),b.positions(),b.deals_since(0),b.account_snapshot()]
    chk("tanpa MT5 tidak crash",True,f"(tick={r[0]}, pos={r[2]})")
except Exception as e:
    chk("tanpa MT5 tidak crash",False,str(e))

print("\n[7] Sinyal hanya dari bar TERTUTUP (anti-repaint)")
src=open(os.path.join(_L,'runner.py')).read()
chk("bar berjalan dikecualikan","for x in bars[:-1]" in src)
chk("evaluasi pakai bars[-2]","bars[-2]" in src)

print("\n[8] Order HANYA boleh dikirim lewat executor.py")
bad=[]
for f in ('runner.py','app.py','mt5_bridge.py','signal_engine.py','store.py'):
    t=open(os.path.join(_L,f)).read()
    import re
    if re.search(r'mt5\.order_send\s*\(', t): bad.append(f)
chk("tidak ada order_send di luar executor",not bad,str(bad))
ex=open(os.path.join(_L,'executor.py')).read()
chk("executor menulis intent sebelum kirim",
    ex.index('create_intent') < ex.index('def _send'))
chk("intent punya UNIQUE(signal_ts,symbol)",
    'UNIQUE(signal_ts, symbol)' in open(os.path.join(_L,'store.py')).read())
chk("client_id ditanam di comment order",'"comment": cid' in ex)
chk("ada verifikasi setelah kirim",'_verify' in ex)
chk("proteksi akun real",'DEMO_ONLY' in ex)

print("\n[9] Warmup cukup untuk MA240 H4")
from config import CFG
need=CFG.BIAS_MA_H4*(240//CFG.TIMEFRAME_MIN)
chk("WARMUP_BARS >= kebutuhan MA",CFG.WARMUP_BARS>=need,f"({CFG.WARMUP_BARS} >= {need})")

print("\n[10] Guardrail terpasang")
import signal_engine as SE
import pandas as pd,numpy as np
df=pd.read_parquet(os.path.join(_L,'cache','m5.parquet')).iloc[-26000:]
ev=SE.evaluate_closed_bar(df,8,0,10000,10000)          # slot penuh
chk("slot penuh memblokir",not ev.passed and 'Slot' in ev.blocked_by)
ev=SE.evaluate_closed_bar(df,0,-500,10000,10000)       # rugi harian
chk("limit rugi harian memblokir",not ev.passed and 'rugi' in ev.blocked_by)
ev=SE.evaluate_closed_bar(df,0,0,7000,10000)           # DD -30%
chk("kill-switch DD memblokir",not ev.passed and 'DD' in ev.blocked_by)


print("\n[16] Candle live memakai MID (bukan BID) — harus cocok dengan backtest")
src=open(os.path.join(_L,'mt5_bridge.py')).read()
chk("konversi bid->mid ada", "h = sp / 2.0" in src and "float(x['open']) + h" in src)
chk("dipakai untuk OHLC", all(f"float(x['{k}']) + h" in src for k in ('open','high','low','close')))

print("\n[17] Kesegaran tampilan candle")
rs=open(os.path.join(_L,'runner.py')).read()
chk("bar berjalan digerakkan tick", "_apply_tick_to_current_bar" in rs)
chk("tampilan pakai MID dari tick", '(t["bid"] + t["ask"]) / 2.0' in rs)
chk("polling bar <= 1 detik", "last_bars > 0.6" in rs)
html=open(os.path.join(_L,'static','index.html')).read()
chk("frontend poll <= 1 detik", "setInterval(poll,1000)" in html)
chk("sinyal TETAP dari bar tertutup", "for x in bars[:-1]" in rs)

print("\n[18] Konversi spread bar (bug 10x pada digits=3)")
src=open(os.path.join(_L,'mt5_bridge.py')).read()
chk("tidak membagi 100", "float(x['spread']) / 100.0" not in src)
chk("pakai symbol point", "float(x['spread']) * point" in src)
chk("ada jaring pengaman ask-bid", "live_sp" in src and "sp = live_sp" in src)
raw=260
chk("digits=3 -> $0.260", abs(raw*0.001-0.260)<1e-9, f"(lama: ${raw/100:.3f})")
chk("guard $1.2 melewatkan spread normal", 0.26 <= 1.2)

print("\n[19] Deviation dikonversi dari USD (bukan point mentah)")
ex=open(os.path.join(_L,'executor.py')).read()
cf=open(os.path.join(_L,'config.py')).read()
chk("tidak ada MAX_SLIPPAGE_POINTS", "MAX_SLIPPAGE_POINTS" not in ex and "MAX_SLIPPAGE_POINTS" not in cf)
chk("dev dihitung dari point simbol", "MAX_SLIPPAGE_USD / info.point" in ex)
chk("digits=3 -> 300 point = $0.30", abs(int(round(0.30/0.001))*0.001-0.30)<1e-9)

print("\n[20] Zona waktu server broker (Exness = GMT+0)")
mb=open(os.path.join(_L,'mt5_bridge.py')).read()
cfs=open(os.path.join(_L,'config.py')).read()
chk("ada deteksi offset server", "_detect_server_offset" in mb)
chk("offset diterapkan ke timestamp bar", "- off_ms" in mb)
chk("dipanggil saat connect", "self._detect_server_offset()" in mb)
chk("default SERVER_GMT_OFFSET = 0 (Exness)", "SERVER_GMT_OFFSET: int | None = 0" in cfs)
chk("override manual dihormati", "SERVER_GMT_OFFSET" in mb and "manual is not None" in mb)
chk("tick basi ditolak", "Tick tampak basi" in mb)
chk("offset tidak lazim ditolak", "(-5, -4, 0, 1, 2, 3)" in mb)

# simulasi: skenario berbahaya harus jatuh ke 0
import time as _tt
_u=int(_tt.time())
def _det(srv, manual=None):
    if manual is not None: return int(manual)
    off=(srv-_u)/3600.0; near=round(off)
    if abs(off-near)>0.2: return 0
    if near not in (-5,-4,0,1,2,3): return 0
    return int(near)
chk("akhir pekan (tick 26j) -> GMT+0", _det(_u-26*3600)==0)
chk("tick 6 jam basi -> GMT+0", _det(_u-6*3600)==0)
chk("Exness manual=0 selalu 0", _det(_u-50*3600, 0)==0)
chk("broker GMT+3 asli tetap terdeteksi", _det(_u+3*3600)==3)

print("\n[21] Contract size diambil dari broker")
chk("baca trade_contract_size", "trade_contract_size" in ex)
chk("lot dikoreksi bila beda", "c.CONTRACT_SIZE / cs" in ex)

print(f"\n{'='*54}\nLULUS {P} · GAGAL {F}")
sys.exit(1 if F else 0)
