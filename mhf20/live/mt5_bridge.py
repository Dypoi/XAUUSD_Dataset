"""Jembatan MetaTrader5 — READ ONLY. Tidak pernah mengirim order.

Tahan gangguan:
  - Auto-resolve nama simbol (Exness: XAUUSDm, XAUUSD, XAUUSD.raw, ...)
  - Auto-reconnect dengan exponential backoff bila terminal/internet putus
  - Semua panggilan dibungkus; kegagalan -> None, bukan crash
  - Mode REPLAY untuk uji tanpa MT5 (mis. di Linux/CI)
"""
import time, threading
from datetime import datetime, timezone, timedelta

try:
    import MetaTrader5 as mt5
    HAVE_MT5 = True
except Exception:
    mt5 = None
    HAVE_MT5 = False

CANDIDATES = ["XAUUSDm", "XAUUSD", "XAUUSD.m", "XAUUSDc", "XAUUSD.raw", "GOLD", "GOLDm"]


class MT5Bridge:
    def __init__(self, symbol_hint="XAUUSDm", logger=None):
        self.symbol = symbol_hint
        self.connected = False
        self.log = logger or (lambda *a, **k: None)
        self._fail = 0
        self._lock = threading.RLock()
        self.account = {}

    # ---------- koneksi ----------
    def connect(self) -> bool:
        if not HAVE_MT5:
            self.log("ERROR", "MT5", "Paket MetaTrader5 tidak tersedia (butuh Windows).")
            return False
        with self._lock:
            try:
                if not mt5.initialize():
                    self.log("WARN", "MT5", f"initialize gagal: {mt5.last_error()}")
                    self.connected = False
                    return False
                ti = mt5.terminal_info(); ai = mt5.account_info()
                if ti is None or ai is None:
                    self.log("WARN", "MT5", "terminal/account info kosong — MT5 sudah login?")
                    self.connected = False
                    return False
                self.account = dict(login=ai.login, server=ai.server, balance=ai.balance,
                                    equity=ai.equity, currency=ai.currency,
                                    leverage=ai.leverage, trade_mode=int(ai.trade_mode))
                if int(ai.trade_mode) == 0:
                    self.log("WARN", "MT5", "AKUN INI REAL, bukan demo. Jurnal dirancang untuk demo.")
                if not self._resolve_symbol():
                    return False
                self.connected = True; self._fail = 0
                self.log("INFO", "MT5", f"Terhubung: {ai.login}@{ai.server} simbol={self.symbol}")
                return True
            except Exception as e:
                self.log("ERROR", "MT5", f"exception connect: {e}")
                self.connected = False
                return False

    def _resolve_symbol(self) -> bool:
        order = [self.symbol] + [c for c in CANDIDATES if c != self.symbol]
        for s in order:
            try:
                if mt5.symbol_info(s) is not None:
                    mt5.symbol_select(s, True)
                    self.symbol = s
                    return True
            except Exception:
                continue
        try:
            for si in (mt5.symbols_get() or []):
                if "XAU" in si.name.upper():
                    mt5.symbol_select(si.name, True); self.symbol = si.name; return True
        except Exception:
            pass
        self.log("ERROR", "MT5", "Simbol XAUUSD tidak ditemukan di Market Watch.")
        return False

    def ensure(self) -> bool:
        """Panggil sebelum tiap operasi. Reconnect dengan backoff."""
        if self.connected:
            try:
                if mt5.terminal_info() is not None:
                    return True
            except Exception:
                pass
            self.connected = False
            self.log("WARN", "MT5", "Koneksi terputus — mencoba menyambung ulang.")
        self._fail += 1
        delay = min(30, 2 ** min(self._fail, 5))
        time.sleep(min(delay, 5))
        return self.connect()

    def shutdown(self):
        try:
            if HAVE_MT5: mt5.shutdown()
        except Exception:
            pass
        self.connected = False

    # ---------- data ----------
    def tick(self):
        if not self.ensure(): return None
        try:
            t = mt5.symbol_info_tick(self.symbol)
            if t is None: return None
            return dict(ts=int(t.time_msc), bid=float(t.bid), ask=float(t.ask),
                        spread=float(t.ask - t.bid))
        except Exception as e:
            self.log("WARN", "MT5", f"tick error: {e}"); self.connected = False; return None

    def bars(self, count=26000, tf_min=5):
        """Ambil bar M5 historis. Dipakai saat start & saat mengisi lubang setelah offline."""
        if not self.ensure(): return None
        try:
            tf = {1: mt5.TIMEFRAME_M1, 5: mt5.TIMEFRAME_M5, 15: mt5.TIMEFRAME_M15}[tf_min]
            r = mt5.copy_rates_from_pos(self.symbol, tf, 0, count)
            if r is None or len(r) == 0: return None
            # MT5 memberi candle harga BID. Backtest MHF-20 memakai MID
            # ((bid+ask)/2). Tanpa konversi ini, sinyal live bergeser sekitar
            # setengah spread terhadap backtest -> bukan sekadar beda tampilan.
            si = mt5.symbol_info(self.symbol)
            point = float(si.point) if si else 0.01
            out = []
            for x in r:
                sp = float(x['spread']) * point      # spread bar dalam USD
                h = sp / 2.0                          # bid -> mid
                out.append(dict(ts=int(x['time']) * 1000,
                                open=float(x['open']) + h, high=float(x['high']) + h,
                                low=float(x['low']) + h, close=float(x['close']) + h,
                                spread=sp, volume=float(x['tick_volume'])))
            return out
        except Exception as e:
            self.log("WARN", "MT5", f"bars error: {e}"); self.connected = False; return None

    def positions(self):
        if not self.ensure(): return []
        try:
            ps = mt5.positions_get(symbol=self.symbol) or []
            return [dict(ticket=int(p.ticket), type=int(p.type), volume=float(p.volume),
                         price_open=float(p.price_open), sl=float(p.sl), tp=float(p.tp),
                         profit=float(p.profit), time=int(p.time) * 1000,
                         symbol=str(p.symbol), magic=int(p.magic),
                         comment=str(p.comment)) for p in ps]
        except Exception as e:
            self.log("WARN", "MT5", f"positions error: {e}"); return []

    def deals_since(self, ts_ms):
        """Deal tertutup — dipakai merekonsiliasi trade yang selesai saat program mati."""
        if not self.ensure(): return []
        try:
            frm = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc) - timedelta(days=1)
            ds = mt5.history_deals_get(frm, datetime.now(timezone.utc) + timedelta(days=1)) or []
            out = []
            for d in ds:
                if self.symbol not in str(d.symbol): continue
                out.append(dict(ticket=int(d.position_id), deal=int(d.ticket),
                                type=int(d.type), entry=int(d.entry), volume=float(d.volume),
                                price=float(d.price), profit=float(d.profit),
                                commission=float(d.commission), swap=float(d.swap),
                                comment=str(d.comment), magic=int(d.magic),
                                time=int(d.time) * 1000))
            return out
        except Exception as e:
            self.log("WARN", "MT5", f"deals error: {e}"); return []

    def account_snapshot(self):
        if not self.ensure(): return self.account
        try:
            a = mt5.account_info()
            if a:
                ti = mt5.terminal_info()
                self.account = dict(login=a.login, server=a.server, balance=float(a.balance),
                                    equity=float(a.equity), margin=float(a.margin),
                                    margin_free=float(a.margin_free), currency=a.currency,
                                    leverage=a.leverage, trade_mode=int(a.trade_mode),
                                    trade_allowed=bool(getattr(ti, 'trade_allowed', True)) and bool(a.trade_allowed))
        except Exception:
            pass
        return self.account


class ReplayBridge:
    """Pengganti MT5 untuk uji di Linux: memutar ulang parquet seolah real-time."""
    def __init__(self, parquet, symbol="XAUUSD-REPLAY", speed=600.0, logger=None):
        import pandas as pd
        self.df = pd.read_parquet(parquet)
        self.symbol = symbol; self.connected = True
        self.log = logger or (lambda *a, **k: None)
        self.speed = speed
        self.i = max(0, len(self.df) - 27000)
        self.t0 = time.time()
        self.account = dict(login=0, server="REPLAY", balance=10000.0, equity=10000.0,
                            currency="USD", leverage=100, trade_mode=1)

    def ensure(self): return True
    def shutdown(self): pass
    def account_snapshot(self): return self.account
    def positions(self): return []
    def deals_since(self, ts): return []

    def _row(self, k):
        r = self.df.iloc[k]
        return dict(ts=int(self.df.index[k].value // 10**6), open=float(r['open']),
                    high=float(r['high']), low=float(r['low']), close=float(r['close']),
                    spread=float(r['spread']), volume=0.0)

    def bars(self, count=26000, tf_min=5):
        cur = min(len(self.df) - 1, self.i + int((time.time() - self.t0) * self.speed / 300))
        return [self._row(k) for k in range(max(0, cur - count), cur + 1)]

    def tick(self):
        b = self.bars(2)[-1]
        return dict(ts=b['ts'], bid=b['close'] - b['spread'] / 2,
                    ask=b['close'] + b['spread'] / 2, spread=b['spread'])


class SimBroker:
    """Broker tiruan untuk menguji jalur EKSEKUSI tanpa MT5.

    Bisa disuruh gagal dengan cara-cara berbahaya:
      fail_mode='none'      normal
      fail_mode='timeout'   order MASUK tapi jawabannya hilang (kasus terburuk)
      fail_mode='reject'    ditolak broker
      fail_mode='silent'    retcode DONE tapi posisi tidak muncul
    """
    def __init__(self):
        self._pos = {}
        self._deals = []
        self._next = 1000
        self.fail_mode = 'none'
        self.sent_count = 0

    def send(self, cid, lot, price, sl, tp):
        self.sent_count += 1
        if self.fail_mode == 'reject':
            return dict(retcode=10006, comment='rejected', ticket=None)
        self._next += 1
        tk = self._next
        if self.fail_mode == 'silent':
            return dict(retcode=10009, comment='done', ticket=tk)   # DONE tanpa posisi
        self._pos[tk] = dict(ticket=tk, type=0, volume=lot, price_open=price, sl=sl, tp=tp,
                             profit=0.0, time=int(time.time()*1000), symbol='SIM',
                             magic=20250904, comment=cid)
        if self.fail_mode == 'timeout':
            raise TimeoutError("koneksi putus setelah order terkirim")
        return dict(retcode=10009, comment='done', ticket=tk)

    def positions(self): return list(self._pos.values())
    def close(self, tk):
        p = self._pos.pop(tk, None)
        if p: self._deals.append(dict(ticket=tk, deal=tk, type=1, entry=1, volume=p['volume'],
                                      price=p['price_open'], profit=0.0, commission=0.0,
                                      swap=0.0, comment=p['comment'], magic=p['magic'],
                                      time=int(time.time()*1000)))
