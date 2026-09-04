"""Runner jurnal MHF-20 — tahan mati listrik, Ctrl+C, dan internet putus.

Siklus pemulihan saat start:
  1. Buka DB (state bertahan dari sesi sebelumnya).
  2. Tarik bar historis dari MT5 -> isi lubang saat program mati (gap-fill).
  3. Rekonsiliasi posisi & deal MT5 vs tabel trades -> tutup yang sudah selesai.
  4. Lanjutkan hari jurnal yang berjalan (tidak mengulang dari nol).
"""
import sys, os, time, threading, signal as sigmod, json, traceback
from datetime import datetime, timezone, timedelta

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [_HERE, os.path.dirname(_HERE)]

import pandas as pd
from config import CFG
from store import Store, now_ms
from executor import Executor
import signal_engine as SE


class Runner:
    def __init__(self, bridge, store: Store):
        self.b = bridge; self.s = store
        self.ex = Executor(bridge, store, CFG, logger=self.log)
        self.stop_flag = threading.Event()
        self.state = dict(status="INIT", last_tick=None, last_bar_ts=None,
                          tick=None, account={}, open_positions=[], day_pnl=0.0,
                          equity=10000.0, peak=10000.0, mt5="DISCONNECTED",
                          last_eval=None, journal_day=1, uptime_start=now_ms(),
                          bars_seen=0, signals_today=0, errors=0)
        self._last_closed_bar = None
        self._thread = None

    def log(self, lvl, kind, msg, payload=None):
        try: self.s.log(lvl, kind, msg, payload)
        except Exception: pass
        print(f"[{datetime.now():%H:%M:%S}] {lvl:5s} {kind:10s} {msg}", flush=True)

    # ---------------- pemulihan ----------------
    def recover(self):
        self.log("INFO", "RECOVER", "Memulai pemulihan state...")
        st = self.s.sget("journal", {})
        if not st:
            st = dict(start_ts=now_ms(), day=1, start_equity=None)
            self.s.sset("journal", st)
            self.log("INFO", "RECOVER", "Jurnal BARU dimulai hari ke-1.")
        else:
            elapsed = (now_ms() - st["start_ts"]) / 86_400_000
            st["day"] = min(CFG.JOURNAL_DAYS, int(elapsed) + 1)
            self.s.sset("journal", st)
            self.log("INFO", "RECOVER", f"Melanjutkan jurnal hari ke-{st['day']} dari {CFG.JOURNAL_DAYS}.")
        self.state["journal_day"] = st["day"]

        last = self.s.last_bar_ts(self.b.symbol)
        if last: self.log("INFO", "RECOVER", f"Bar terakhir di DB: {datetime.utcfromtimestamp(last/1000)} UTC")

        bars = self.b.bars(CFG.WARMUP_BARS, CFG.TIMEFRAME_MIN)
        if bars:
            new = 0
            for x in bars:
                if last is None or x["ts"] > last: new += 1
                self.s.upsert_bar(self.b.symbol, x["ts"], x["open"], x["high"], x["low"],
                                  x["close"], x["spread"], x["volume"])
            self.log("INFO", "RECOVER", f"Gap-fill: {len(bars):,} bar disinkronkan, {new:,} baru.")
        else:
            self.log("WARN", "RECOVER", "Tidak bisa menarik bar dari MT5 — jalan dengan data DB.")

        self.reconcile()
        acc = self.b.account_snapshot()
        if acc:
            self.state["account"] = acc
            eq = float(acc.get("equity", 10000.0))
            self.state["equity"] = eq
            if st.get("start_equity") is None:
                st["start_equity"] = eq; self.s.sset("journal", st)
            self.state["peak"] = max(self.s.sget("peak_equity", eq), eq)
        # WAJIB sebelum entry baru: pastikan tak ada order yang nasibnya menggantung
        self.ex.reconcile_intents()
        self.state["frozen"] = self.ex.frozen
        self.state["freeze_reason"] = self.ex.freeze_reason
        self.log("INFO", "RECOVER", "Pemulihan selesai.")

    def reconcile(self):
        """Samakan tabel trades dengan kenyataan di MT5. Idempotent."""
        try:
            pos = self.b.positions()
            live_tickets = {p["ticket"] for p in pos}
            for p in pos:
                self.s.upsert_trade(ticket=p["ticket"], symbol=self.b.symbol,
                                    direction="BUY" if p["type"] == 0 else "SELL",
                                    entry_ts=p["time"], entry_price=p["price_open"],
                                    lot=p["volume"], sl=p["sl"], status="OPEN")
            for t in self.s.open_trades():
                if t["ticket"] and t["ticket"] not in live_tickets:
                    pnl = None
                    for d in self.b.deals_since(t["entry_ts"] or now_ms() - 7 * 86_400_000):
                        if d["ticket"] == t["ticket"] and d["entry"] == 1:
                            pnl = d["profit"] + d["commission"] + d["swap"]
                            self.s.upsert_trade(ticket=t["ticket"], exit_ts=d["time"],
                                                exit_price=d["price"], pnl=pnl,
                                                status="CLOSED", reason="MT5")
                            break
                    if pnl is None:
                        self.s.upsert_trade(ticket=t["ticket"], status="CLOSED",
                                            reason="HILANG_DARI_MT5", exit_ts=now_ms())
                    self.log("INFO", "RECONCILE", f"Trade #{t['ticket']} ditutup (pnl={pnl}).")
            self.state["open_positions"] = pos
        except Exception as e:
            self.log("WARN", "RECONCILE", f"gagal: {e}")

    # ---------------- loop utama ----------------
    def loop(self):
        self.state["status"] = "RUNNING"
        last_beat = 0; last_recon = 0; last_bars = 0; last_manage = 0
        while not self.stop_flag.is_set():
            try:
                t = self.b.tick()
                if t:
                    self.state["tick"] = t
                    self.state["last_tick"] = now_ms()
                    self.state["mt5"] = "CONNECTED"
                    self._apply_tick_to_current_bar(t)
                else:
                    self.state["mt5"] = "RECONNECTING"

                if time.time() - last_bars > 0.6:
                    last_bars = time.time()
                    self._poll_bars()

                if time.time() - last_manage > CFG.MANAGE_INTERVAL_S:
                    last_manage = time.time()
                    self.ex.manage_positions()
                    if self.ex.frozen and not self.state.get("frozen"):
                        self.ex.reconcile_intents()
                    self.state["frozen"] = self.ex.frozen
                    self.state["freeze_reason"] = self.ex.freeze_reason
                    self.state["orders_today"] = self.ex.orders_today

                if time.time() - last_recon > 10:
                    last_recon = time.time()
                    self.reconcile()
                    acc = self.b.account_snapshot()
                    if acc:
                        self.state["account"] = acc
                        eq = float(acc.get("equity", self.state["equity"]))
                        self.state["equity"] = eq
                        if eq > self.state["peak"]:
                            self.state["peak"] = eq; self.s.sset("peak_equity", eq)
                    self._update_day_pnl()

                if time.time() - last_beat > CFG.HEARTBEAT_SEC:
                    last_beat = time.time()
                    self.s.beat("main", dict(status=self.state["status"], mt5=self.state["mt5"],
                                             equity=self.state["equity"],
                                             day=self.state["journal_day"]))
                lt = self.state["last_tick"]
                if lt and (now_ms() - lt) / 1000 > CFG.STALE_TICK_SEC:
                    self.state["status"] = "DEGRADED"
                elif self.state["mt5"] == "CONNECTED":
                    self.state["status"] = "RUNNING"

                time.sleep(CFG.TICK_POLL_MS / 1000)
            except Exception as e:
                self.state["errors"] += 1
                self.log("ERROR", "LOOP", f"{e}", dict(tb=traceback.format_exc()[-1500:]))
                time.sleep(2)
        self.state["status"] = "STOPPED"
        self.log("INFO", "SHUTDOWN", "Loop berhenti bersih. State tersimpan.")

    def _poll_bars(self):
        bars = self.b.bars(400, CFG.TIMEFRAME_MIN)
        if not bars: return
        for x in bars[:-1]:      # bar terakhir masih berjalan -> jangan dipakai sinyal
            self.s.upsert_bar(self.b.symbol, x["ts"], x["open"], x["high"], x["low"],
                              x["close"], x["spread"], x["volume"])
        cur = bars[-1]
        self.state["bars_seen"] = len(bars)
        self.state["current_bar"] = cur
        closed_ts = bars[-2]["ts"] if len(bars) > 1 else None
        self.state["last_bar_ts"] = closed_ts
        if closed_ts and closed_ts != self._last_closed_bar:
            self._last_closed_bar = closed_ts
            self._on_bar_close()

    def _apply_tick_to_current_bar(self, t):
        """Gerakkan bar berjalan mengikuti tick (tanpa menunggu polling bar).

        Dipakai HANYA untuk tampilan. Sinyal tetap dihitung dari bar tertutup.
        Harga disamakan ke MID agar konsisten dengan backtest.
        """
        cur = self.state.get("current_bar")
        if not cur:
            return
        mid = (t["bid"] + t["ask"]) / 2.0
        bar_ms = CFG.TIMEFRAME_MIN * 60 * 1000
        slot = (t["ts"] // bar_ms) * bar_ms
        if slot > cur["ts"]:
            # bar baru terbentuk sebelum polling sempat jalan
            cur = dict(ts=slot, open=mid, high=mid, low=mid, close=mid,
                       spread=t["spread"], volume=0.0)
        else:
            cur = dict(cur)
            cur["close"] = mid
            cur["high"] = max(cur["high"], mid)
            cur["low"] = min(cur["low"], mid)
            cur["spread"] = t["spread"]
        self.state["current_bar"] = cur

    def _on_bar_close(self):
        rows = self.s.bars(self.b.symbol, CFG.WARMUP_BARS)
        df = SE.build_frame(rows)
        if df.empty: return
        ev = SE.evaluate_closed_bar(df, len(self.state["open_positions"]),
                                    self.state["day_pnl"], self.state["equity"],
                                    self.state["peak"])
        self.state["last_eval"] = dict(ts=ev.ts, price=ev.price, spread=ev.spread,
                                       passed=ev.passed, reasons=ev.reasons,
                                       blocked_by=ev.blocked_by, lot=ev.lot, sl=ev.sl,
                                       tp1=ev.tp1, tp2=ev.tp2, ctx=ev.ctx)
        if ev.ts:
            self.s.add_signal(self.b.symbol, ev.ts, ev.price, ev.spread, ev.lot, ev.sl,
                              ev.tp1, ev.tp2, ev.passed, ev.reasons, ev.blocked_by)
        if ev.passed:
            self.state["signals_today"] += 1
            self.log("INFO", "SIGNAL",
                     f"ENTRY VALID @ {ev.price:.2f} lot={ev.lot} SL={ev.sl:.2f} TP2={ev.tp2:.2f}")
            r = self.ex.execute(ev, len(self.state["open_positions"]),
                                self.state["day_pnl"], self.state["equity"], self.state["peak"])
            self.state["last_exec"] = r
            self.state["frozen"] = self.ex.frozen
            self.state["freeze_reason"] = self.ex.freeze_reason
            if not r.get("ok"):
                self.log("WARN", "EXEC", f"Tidak dieksekusi: {r.get('reason')}")
            else:
                self.reconcile()

    def _update_day_pnl(self):
        try:
            d0 = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            ms = int(d0.timestamp() * 1000)
            tot = sum(t["pnl"] or 0 for t in self.s.trades(500)
                      if t["status"] == "CLOSED" and (t["exit_ts"] or 0) >= ms)
            tot += sum(p["profit"] for p in self.state["open_positions"])
            self.state["day_pnl"] = tot
        except Exception:
            pass

    def start(self):
        self.recover()
        self._thread = threading.Thread(target=self.loop, daemon=True)
        self._thread.start()

    def stop(self):
        self.log("INFO", "SHUTDOWN", "Sinyal berhenti diterima — menyimpan state...")
        self.stop_flag.set()
        if self._thread: self._thread.join(timeout=10)
        try: self.b.shutdown()
        except Exception: pass
        self.s.log("INFO", "SHUTDOWN", "Bersih.")
        self.s.close()
