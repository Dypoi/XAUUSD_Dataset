"""Persistensi crash-safe untuk jurnal MHF-20.

Desain tahan-mati:
  - SQLite mode WAL: commit atomik, selamat dari kill -9 / cabut listrik.
  - Setiap tulisan langsung commit. Tidak ada state penting yang cuma di RAM.
  - Semua insert IDEMPOTENT lewat UNIQUE key -> restart/reconnect tidak menggandakan data.
  - Bar disimpan mentah; sinyal disimpan beserta SNAPSHOT ALASAN (JSON) agar bisa diaudit.
"""
import sqlite3, json, os, time, threading
from contextlib import contextmanager
from datetime import datetime, timezone

_LOCK = threading.RLock()

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=FULL;

CREATE TABLE IF NOT EXISTS bars(
  ts INTEGER NOT NULL, symbol TEXT NOT NULL,
  open REAL, high REAL, low REAL, close REAL, spread REAL, volume REAL,
  PRIMARY KEY(symbol, ts)
);

CREATE TABLE IF NOT EXISTS signals(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts INTEGER NOT NULL, symbol TEXT NOT NULL,
  price REAL, spread REAL, lot REAL, sl REAL, tp1 REAL, tp2 REAL,
  passed INTEGER,           -- 1 = semua syarat lolos (entry valid)
  reasons TEXT,             -- JSON: tiap syarat + nilai + lolos/tidak
  blocked_by TEXT,          -- alasan penolakan bila passed=0
  UNIQUE(symbol, ts)
);

CREATE TABLE IF NOT EXISTS trades(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  signal_id INTEGER, ticket INTEGER UNIQUE,      -- ticket MT5, kunci rekonsiliasi
  symbol TEXT, direction TEXT,
  entry_ts INTEGER, entry_price REAL, lot REAL,
  sl REAL, tp1 REAL, tp2 REAL,
  exit_ts INTEGER, exit_price REAL, pnl REAL, reason TEXT,
  status TEXT DEFAULT 'OPEN',
  note TEXT
);

CREATE TABLE IF NOT EXISTS events(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts INTEGER, level TEXT, kind TEXT, msg TEXT, payload TEXT
);

CREATE TABLE IF NOT EXISTS heartbeat(
  k TEXT PRIMARY KEY, ts INTEGER, payload TEXT
);

CREATE TABLE IF NOT EXISTS session(
  k TEXT PRIMARY KEY, v TEXT
);

-- ====================================================================
-- INTENT: write-ahead log untuk order. INTI ANTI-DUPLIKASI.
-- Baris ditulis + di-commit SEBELUM order dikirim ke MT5. Kalau proses
-- mati kapan pun setelah itu, saat restart kita tahu ada order yang
-- statusnya belum pasti dan wajib direkonsiliasi sebelum kirim apa pun.
-- client_id unik = kunci idempotensi (juga ditanam di comment MT5).
-- ====================================================================
CREATE TABLE IF NOT EXISTS intents(
  client_id TEXT PRIMARY KEY,     -- mis. MHF20-<bar_ts>-<nonce>
  signal_ts INTEGER NOT NULL,     -- bar sinyal; 1 bar = maksimal 1 intent
  symbol TEXT, direction TEXT,
  lot REAL, sl REAL, tp REAL,
  requested_ts INTEGER,           -- kapan intent ditulis (sebelum kirim)
  sent_ts INTEGER,                -- kapan order_send benar-benar dipanggil
  state TEXT NOT NULL,            -- PENDING|SENT|FILLED|REJECTED|ORPHAN|RESOLVED|ABANDONED
  ticket INTEGER,                 -- diisi setelah fill terkonfirmasi
  retcode INTEGER, comment TEXT,
  fill_price REAL, attempts INTEGER DEFAULT 0,
  last_error TEXT,
  UNIQUE(signal_ts, symbol)       -- 1 bar sinyal = 1 order. Anti-dobel struktural.
);
CREATE INDEX IF NOT EXISTS ix_intent_state ON intents(state);

CREATE INDEX IF NOT EXISTS ix_bars_ts ON bars(ts);
CREATE INDEX IF NOT EXISTS ix_sig_ts ON signals(ts);
CREATE INDEX IF NOT EXISTS ix_ev_ts ON events(ts);
"""


def now_ms() -> int:
    return int(time.time() * 1000)


class Store:
    def __init__(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.path = path
        self._c = sqlite3.connect(path, check_same_thread=False, timeout=30.0)
        self._c.row_factory = sqlite3.Row
        with _LOCK:
            self._c.executescript(SCHEMA)
            self._c.commit()

    @contextmanager
    def tx(self):
        with _LOCK:
            try:
                yield self._c
                self._c.commit()
            except Exception:
                self._c.rollback()
                raise

    # ---------- bars ----------
    def upsert_bar(self, symbol, ts, o, h, l, c, spread, vol=0.0):
        with self.tx() as cx:
            cx.execute("""INSERT INTO bars(ts,symbol,open,high,low,close,spread,volume)
                          VALUES(?,?,?,?,?,?,?,?)
                          ON CONFLICT(symbol,ts) DO UPDATE SET
                            high=max(high,excluded.high), low=min(low,excluded.low),
                            close=excluded.close, spread=excluded.spread,
                            volume=excluded.volume""",
                       (int(ts), symbol, o, h, l, c, spread, vol))

    def bars(self, symbol, limit=1500):
        cur = self._c.execute(
            "SELECT ts,open,high,low,close,spread FROM bars WHERE symbol=? ORDER BY ts DESC LIMIT ?",
            (symbol, limit))
        return [dict(r) for r in cur.fetchall()][::-1]

    def last_bar_ts(self, symbol):
        r = self._c.execute("SELECT max(ts) t FROM bars WHERE symbol=?", (symbol,)).fetchone()
        return r["t"]

    # ---------- signals ----------
    def add_signal(self, symbol, ts, price, spread, lot, sl, tp1, tp2,
                   passed, reasons, blocked_by=""):
        with self.tx() as cx:
            cx.execute("""INSERT OR IGNORE INTO signals
                (ts,symbol,price,spread,lot,sl,tp1,tp2,passed,reasons,blocked_by)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (int(ts), symbol, price, spread, lot, sl, tp1, tp2,
                 1 if passed else 0, json.dumps(reasons, ensure_ascii=False), blocked_by))
        r = self._c.execute("SELECT id FROM signals WHERE symbol=? AND ts=?",
                            (symbol, int(ts))).fetchone()
        return r["id"] if r else None

    def signals(self, limit=200, only_passed=False):
        q = "SELECT * FROM signals {} ORDER BY ts DESC LIMIT ?".format(
            "WHERE passed=1" if only_passed else "")
        rows = [dict(r) for r in self._c.execute(q, (limit,)).fetchall()]
        for r in rows:
            try: r["reasons"] = json.loads(r["reasons"] or "[]")
            except Exception: r["reasons"] = []
        return rows

    # ---------- trades ----------
    def upsert_trade(self, **kw):
        """Idempotent lewat ticket MT5 — reconnect tidak menggandakan trade."""
        cols = ("signal_id","ticket","symbol","direction","entry_ts","entry_price","lot",
                "sl","tp1","tp2","exit_ts","exit_price","pnl","reason","status","note")
        d = {k: kw.get(k) for k in cols}
        with self.tx() as cx:
            if d["ticket"] is not None:
                ex = cx.execute("SELECT id FROM trades WHERE ticket=?", (d["ticket"],)).fetchone()
                if ex:
                    sets = ",".join(f"{k}=?" for k in cols if d[k] is not None)
                    vals = [d[k] for k in cols if d[k] is not None] + [d["ticket"]]
                    cx.execute(f"UPDATE trades SET {sets} WHERE ticket=?", vals)
                    return ex["id"]
            cur = cx.execute(
                f"INSERT INTO trades({','.join(cols)}) VALUES({','.join('?'*len(cols))})",
                [d[k] for k in cols])
            return cur.lastrowid

    def trades(self, limit=500):
        return [dict(r) for r in self._c.execute(
            "SELECT * FROM trades ORDER BY COALESCE(entry_ts,0) DESC LIMIT ?", (limit,)).fetchall()]

    def open_trades(self):
        return [dict(r) for r in self._c.execute(
            "SELECT * FROM trades WHERE status='OPEN'").fetchall()]

    # ---------- events ----------
    def log(self, level, kind, msg, payload=None):
        with self.tx() as cx:
            cx.execute("INSERT INTO events(ts,level,kind,msg,payload) VALUES(?,?,?,?,?)",
                       (now_ms(), level, kind, msg,
                        json.dumps(payload, ensure_ascii=False) if payload else None))

    def events(self, limit=300):
        return [dict(r) for r in self._c.execute(
            "SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]

    # ---------- heartbeat / session ----------
    def beat(self, key="main", payload=None):
        with self.tx() as cx:
            cx.execute("""INSERT INTO heartbeat(k,ts,payload) VALUES(?,?,?)
                          ON CONFLICT(k) DO UPDATE SET ts=excluded.ts,payload=excluded.payload""",
                       (key, now_ms(), json.dumps(payload or {})))

    def last_beat(self, key="main"):
        r = self._c.execute("SELECT ts,payload FROM heartbeat WHERE k=?", (key,)).fetchone()
        return dict(r) if r else None

    def sset(self, k, v):
        with self.tx() as cx:
            cx.execute("""INSERT INTO session(k,v) VALUES(?,?)
                          ON CONFLICT(k) DO UPDATE SET v=excluded.v""", (k, json.dumps(v)))

    def sget(self, k, default=None):
        r = self._c.execute("SELECT v FROM session WHERE k=?", (k,)).fetchone()
        if not r: return default
        try: return json.loads(r["v"])
        except Exception: return default

    # ---------- intents (write-ahead order log) ----------
    def create_intent(self, client_id, signal_ts, symbol, direction, lot, sl, tp):
        """Tulis + COMMIT intent SEBELUM order dikirim.

        Return None bila bar sinyal ini sudah punya intent (anti-dobel struktural).
        """
        try:
            with self.tx() as cx:
                cx.execute("""INSERT INTO intents(client_id,signal_ts,symbol,direction,lot,sl,tp,
                              requested_ts,state,attempts)
                              VALUES(?,?,?,?,?,?,?,?, 'PENDING',0)""",
                           (client_id, int(signal_ts), symbol, direction, lot, sl, tp, now_ms()))
            return client_id
        except sqlite3.IntegrityError:
            return None

    def mark_intent(self, client_id, **kw):
        if not kw: return
        sets = ",".join(f"{k}=?" for k in kw)
        with self.tx() as cx:
            cx.execute(f"UPDATE intents SET {sets} WHERE client_id=?",
                       list(kw.values()) + [client_id])

    def intent(self, client_id):
        r = self._c.execute("SELECT * FROM intents WHERE client_id=?", (client_id,)).fetchone()
        return dict(r) if r else None

    def intent_for_bar(self, symbol, signal_ts):
        r = self._c.execute("SELECT * FROM intents WHERE symbol=? AND signal_ts=?",
                            (symbol, int(signal_ts))).fetchone()
        return dict(r) if r else None

    def unresolved_intents(self):
        """Intent yang nasibnya belum pasti — WAJIB diselesaikan saat startup."""
        return [dict(r) for r in self._c.execute(
            "SELECT * FROM intents WHERE state IN ('PENDING','SENT','ORPHAN') ORDER BY requested_ts"
        ).fetchall()]

    def intents(self, limit=200):
        return [dict(r) for r in self._c.execute(
            "SELECT * FROM intents ORDER BY requested_ts DESC LIMIT ?", (limit,)).fetchall()]

    def close(self):
        with _LOCK:
            try: self._c.commit(); self._c.close()
            except Exception: pass
