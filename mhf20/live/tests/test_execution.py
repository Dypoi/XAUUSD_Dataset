"""AUDIT FORENSIK 3 — Jalur EKSEKUSI ORDER.

Fokus pada kegagalan yang bisa menyebabkan POSISI DOBEL atau POSISI YATIM.
Broker tiruan disuruh gagal dengan cara paling berbahaya, lalu kita buktikan
sistem tidak pernah mengirim order kedua untuk sinyal yang sama.
"""
import sys, os, time, types
_L = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_M = os.path.dirname(_L)
sys.path[:0] = [_L, _M]

from store import Store, now_ms
from mt5_bridge import SimBroker
import executor as EX
from config import CFG

P = F = 0
def chk(n, c, i=""):
    global P, F
    if c: P += 1; print(f"  LULUS  {n} {i}")
    else: F += 1; print(f"  GAGAL  {n} {i}")

DB = '/tmp/exec.db'
for f in (DB, DB+'-wal', DB+'-shm'):
    if os.path.exists(f): os.remove(f)


class FakeBridge:
    def __init__(self, sim):
        self.sim = sim; self.symbol = 'SIM'; self.connected = True
    def ensure(self): return self.connected
    def positions(self): return self.sim.positions()
    def deals_since(self, ts): return self.sim._deals
    def account_snapshot(self):
        return dict(trade_mode=1, trade_allowed=True, margin_free=5000.0,
                    equity=10000.0, balance=10000.0)


class Ev:
    def __init__(self, ts, price=3300.0):
        self.ts = ts; self.price = price; self.spread = 0.35
        self.lot = 0.16; self.sl = price - 12; self.tp2 = price + 24
        self.passed = True


def patch(sim):
    """Ganti panggilan MT5 di executor dengan broker tiruan."""
    EX.HAVE_MT5 = True
    m = types.SimpleNamespace()
    m.TRADE_ACTION_DEAL = 1; m.TRADE_ACTION_SLTP = 2
    m.ORDER_TYPE_BUY = 0; m.ORDER_TYPE_SELL = 1
    m.ORDER_TIME_GTC = 0
    m.ORDER_FILLING_FOK = 1; m.ORDER_FILLING_IOC = 2; m.ORDER_FILLING_RETURN = 3
    m.TRADE_RETCODE_DONE = 10009
    m.symbol_info_tick = lambda s: types.SimpleNamespace(bid=3299.65, ask=3300.0)
    m.symbol_info = lambda s: types.SimpleNamespace(
        digits=2, point=0.01, trade_stops_level=0, volume_min=0.01,
        volume_max=50.0, volume_step=0.01, filling_mode=1)
    m.last_error = lambda: (0, 'ok')
    def order_send(req):
        r = sim.send(req['comment'], req['volume'], req['price'], req['sl'], req['tp'])
        return types.SimpleNamespace(retcode=r['retcode'], comment=r['comment'],
                                     order=r['ticket'] or 0)
    m.order_send = order_send
    EX.mt5 = m
    return m


print("\n[1] Order normal: 1 sinyal -> tepat 1 order")
s = Store(DB); sim = SimBroker(); b = FakeBridge(sim); patch(sim)
ex = EX.Executor(b, s, CFG, logger=lambda *a, **k: None)
r = ex.execute(Ev(1000), 0, 0, 10000, 10000)
chk("order tereksekusi", r.get('ok'), f"(ticket {r.get('ticket')})")
chk("broker menerima 1 order", sim.sent_count == 1, f"({sim.sent_count})")
chk("intent FILLED", s.intent_for_bar('SIM', 1000)['state'] == 'FILLED')

print("\n[2] SINYAL SAMA DUA KALI -> order kedua HARUS ditolak")
r2 = ex.execute(Ev(1000), 1, 0, 10000, 10000)
chk("order kedua ditolak", not r2.get('ok'), f"({r2.get('reason')})")
chk("broker tetap 1 order", sim.sent_count == 1, f"({sim.sent_count})")

print("\n[3] KASUS TERBURUK: order MASUK tapi jawaban hilang, lalu proses MATI")
ex.orders_today = 0   # skenario ini menguji orphan, bukan cap harian
sim.fail_mode = 'timeout'
r3 = ex.execute(Ev(2000), 1, 0, 10000, 10000)
chk("dilaporkan gagal", not r3.get('ok'))
chk("sistem DIBEKUKAN", ex.frozen, f"({ex.freeze_reason})")
chk("intent jadi ORPHAN", s.intent_for_bar('SIM', 2000)['state'] == 'ORPHAN')
chk("posisi memang terlanjur ada di broker", len(sim.positions()) == 2)
before = sim.sent_count
del s, ex                                  # meniru proses mati mendadak

print("\n[4] RESTART: harus menemukan posisi yatim, TIDAK mengirim ulang")
s2 = Store(DB)
ex2 = EX.Executor(b, s2, CFG, logger=lambda *a, **k: None)
sim.fail_mode = 'none'
ex2.reconcile_intents()
it = s2.intent_for_bar('SIM', 2000)
chk("intent yatim dikenali sebagai FILLED", it['state'] == 'FILLED', f"({it['state']})")
chk("ticket tercatat", it['ticket'] is not None, f"(#{it['ticket']})")
chk("TIDAK ada order baru", sim.sent_count == before, f"({sim.sent_count} vs {before})")
chk("beku dicabut", not ex2.frozen)
chk("total posisi tetap 2", len(sim.positions()) == 2, f"({len(sim.positions())})")

print("\n[5] Sinyal sama setelah restart -> tetap tidak dobel")
r5 = ex2.execute(Ev(2000), 2, 0, 10000, 10000)
chk("ditolak", not r5.get('ok'), f"({r5.get('reason')})")
chk("broker tetap {} order".format(before), sim.sent_count == before)

print("\n[6] Broker menolak (retcode fatal) -> tidak diulang, tidak beku")
sim.fail_mode = 'reject'
n0 = sim.sent_count
ex2.orders_today = 0            # isolasi: uji kegagalan broker, bukan cap harian
r6 = ex2.execute(Ev(3000), 0, 0, 10000, 10000)
chk("dilaporkan gagal", not r6.get('ok'))
chk("intent REJECTED", s2.intent_for_bar('SIM', 3000)['state'] == 'REJECTED')
chk("hanya 1 percobaan", sim.sent_count == n0 + 1, f"({sim.sent_count-n0})")
chk("tidak membekukan sistem", not ex2.frozen)

print("\n[7] Broker bilang DONE tapi posisi tak terlihat -> BEKU, tidak menebak")
sim.fail_mode = 'silent'
ex2.frozen = False
ex2.orders_today = 0            # isolasi: uji jawaban hilang, bukan cap harian
r7 = ex2.execute(Ev(4000), 0, 0, 10000, 10000)
chk("dilaporkan gagal", not r7.get('ok'))
chk("sistem dibekukan", ex2.frozen, f"({ex2.freeze_reason})")
chk("intent ORPHAN", s2.intent_for_bar('SIM', 4000)['state'] == 'ORPHAN')

print("\n[8] Selama BEKU, entry baru diblokir total")
ok, why = ex2.can_execute(Ev(5000), 0, 0, 10000, 10000)
chk("entry baru diblokir", not ok, f"({why})")

print("\n[9] Semua gerbang risiko")
sim.fail_mode = 'none'
ex2.frozen = False; ex2.freeze_reason = ''
cases = [
    ("slot penuh",        dict(n=8,  d=0,    e=10000, p=10000), "Slot penuh"),
    ("rugi harian",       dict(n=0,  d=-350, e=10000, p=10000), "rugi harian"),
    ("target profit",     dict(n=0,  d=600,  e=10000, p=10000), "profit harian"),
    ("kill-switch DD",    dict(n=0,  d=0,    e=7500,  p=10000), "drawdown"),
]
for nm, kw, expect in cases:
    ok, why = ex2.can_execute(Ev(9000), kw['n'], kw['d'], kw['e'], kw['p'])
    chk(nm + " memblokir", (not ok) and expect.lower() in why.lower(), f"({why})")

ev = Ev(9100); ev.spread = 2.0
ok, why = ex2.can_execute(ev, 0, 0, 10000, 10000)
chk("spread lebar memblokir", not ok, f"({why})")

print("\n[10] Proteksi AKUN REAL")
class RealBridge(FakeBridge):
    def account_snapshot(self):
        return dict(trade_mode=0, trade_allowed=True, margin_free=5000.0)
ex3 = EX.Executor(RealBridge(sim), s2, CFG, logger=lambda *a, **k: None)
ok, why = ex3.can_execute(Ev(9200), 0, 0, 10000, 10000)
chk("akun REAL diblokir", not ok and 'REAL' in why, f"({why})")

print("\n[11] AutoTrading mati di terminal")
class NoTrade(FakeBridge):
    def account_snapshot(self):
        return dict(trade_mode=1, trade_allowed=False, margin_free=5000.0)
ex4 = EX.Executor(NoTrade(sim), s2, CFG, logger=lambda *a, **k: None)
ok, why = ex4.can_execute(Ev(9300), 0, 0, 10000, 10000)
chk("diblokir saat AutoTrading mati", not ok, f"({why})")

print("\n[12] Margin bebas menipis")
class LowMargin(FakeBridge):
    def account_snapshot(self):
        return dict(trade_mode=1, trade_allowed=True, margin_free=50.0)
ex5 = EX.Executor(LowMargin(sim), s2, CFG, logger=lambda *a, **k: None)
ok, why = ex5.can_execute(Ev(9400), 0, 0, 10000, 10000)
chk("diblokir margin tipis", not ok and 'argin' in why, f"({why})")

print("\n[13] Batas order per hari")
ex2.orders_today = CFG.MAX_ENTRIES_PER_DAY
ex2.frozen = False
ok13, why13 = ex2.can_execute(Ev(9450), 0, 0, 10000, 10000)
chk("mode santai: entry ke-2 hari sama ditolak", (not ok13) and "santai" in why13.lower())
ex2.orders_today = CFG.MAX_ORDERS_PER_DAY
ok, why = ex2.can_execute(Ev(9500), 0, 0, 10000, 10000)
chk("batas harian memblokir", not ok, f"({why})")
ex2.orders_today = 0

print("\n[14] MT5 putus saat mengirim -> tidak crash")
b.connected = False
r14 = ex2.execute(Ev(9600), 0, 0, 10000, 10000)
chk("gagal dengan rapi", not r14.get('ok'), f"({r14.get('reason')})")
b.connected = True

print("\n[15] Integritas DB setelah semua skenario")
import sqlite3
c = sqlite3.connect(DB)
chk("integrity_check ok", c.execute("PRAGMA integrity_check").fetchone()[0] == 'ok')
dup = c.execute("SELECT COUNT(*)-COUNT(DISTINCT signal_ts||symbol) FROM intents").fetchone()[0]
chk("nol intent dobel per bar", dup == 0, f"({dup})")
n_pos = len(sim.positions())
n_fill = c.execute("SELECT COUNT(*) FROM intents WHERE state='FILLED'").fetchone()[0]
chk("posisi broker == intent FILLED", n_pos == n_fill, f"(broker {n_pos} vs filled {n_fill})")

print(f"\n{'='*56}\nLULUS {P} · GAGAL {F}")
sys.exit(1 if F else 0)
