"""Eksekusi order MHF-20 — tingkat produksi, tahan crash & putus koneksi.

=========================== MODEL KEGAGALAN ===========================
Bahaya terbesar auto-execute bukan "order gagal" (itu mudah: coba lagi).
Bahaya terbesar adalah **order berhasil tapi kita tidak tahu** — proses mati
setelah order_send terkirim tapi sebelum jawabannya tercatat. Kalau saat
restart kita main kirim lagi, posisi jadi dobel.

Solusi: WRITE-AHEAD INTENT + IDENTITAS UNIK
  1. Tulis intent ke SQLite dan COMMIT  <-- sebelum menyentuh MT5
  2. Tanam client_id ke comment order + magic number
  3. Kirim order
  4. Catat hasilnya
Kalau mati di antara langkah manapun, saat startup setiap intent yang belum
pasti DICOCOKKAN ke posisi/deal nyata di MT5 lewat client_id. Tidak pernah
kirim ulang tanpa membuktikan order lama tidak ada.

Pengaman lain:
  - UNIQUE(signal_ts, symbol): 1 bar sinyal = 1 order, dijamin oleh DB
  - Kill-switch: rugi harian, DD, spread, slot, dan batas order/hari
  - Verifikasi setelah kirim: retcode + posisi benar-benar ada
  - Batas percobaan; retcode fatal tidak diulang
  - RECON-FIRST: selama masih ada intent belum jelas, entry baru DIBEKUKAN
=======================================================================
"""
import time, uuid, threading
from datetime import datetime, timezone

try:
    import MetaTrader5 as mt5
    HAVE_MT5 = True
except Exception:
    mt5 = None
    HAVE_MT5 = False

MAGIC = 20250904

# retcode yang tidak ada gunanya diulang
FATAL = {
    10004,  # requote
    10006,  # rejected
    10013,  # invalid request
    10014,  # invalid volume
    10015,  # invalid price
    10016,  # invalid stops
    10017,  # trade disabled
    10018,  # market closed
    10019,  # no money
    10027,  # autotrading disabled by client
    10032,  # only real accounts allowed
}
RETRYABLE = {10008, 10009, 10010, 10021, 10024, 10030, 10031}


class Executor:
    """Read-write ke MT5. Semua jalur menulis melewati kelas ini."""

    def __init__(self, bridge, store, cfg, logger=None):
        self.b = bridge
        self.s = store
        self.cfg = cfg
        self.log = logger or (lambda *a, **k: None)
        self._lock = threading.RLock()
        self.frozen = False           # dibekukan bila ada intent tak jelas
        self.freeze_reason = ""
        self.last_error = ""
        self.orders_today = 0
        self._day = None

    # ------------------------------------------------------------------
    # STARTUP: selesaikan semua intent yang nasibnya belum pasti
    # ------------------------------------------------------------------
    def reconcile_intents(self):
        """WAJIB dipanggil saat startup, SEBELUM entry baru diizinkan."""
        pend = self.s.unresolved_intents()
        if not pend:
            self.frozen = False
            self.freeze_reason = ""
            return
        self.log("WARN", "RECON", f"{len(pend)} intent belum pasti — mencocokkan ke MT5.")
        self.frozen = True
        self.freeze_reason = f"{len(pend)} intent menunggu rekonsiliasi"

        positions = {}
        deals = {}
        try:
            for p in self.b.positions():
                cid = self._cid_from_comment(p.get("comment", ""))
                if cid: positions[cid] = p
            oldest = min(i["requested_ts"] for i in pend)
            for d in self.b.deals_since(oldest - 3600_000):
                cid = self._cid_from_comment(d.get("comment", ""))
                if cid: deals.setdefault(cid, d)
        except Exception as e:
            self.log("ERROR", "RECON", f"Tidak bisa membaca MT5: {e}. Tetap beku demi keamanan.")
            return

        for it in pend:
            cid = it["client_id"]
            age_s = (int(time.time() * 1000) - it["requested_ts"]) / 1000
            if cid in positions:
                p = positions[cid]
                self.s.mark_intent(cid, state="FILLED", ticket=p["ticket"],
                                   fill_price=p["price_open"])
                self.s.upsert_trade(ticket=p["ticket"], symbol=p["symbol"] if "symbol" in p else self.b.symbol,
                                    direction="BUY", entry_ts=p["time"],
                                    entry_price=p["price_open"], lot=p["volume"],
                                    sl=p["sl"], status="OPEN", note=f"recon:{cid}")
                self.log("INFO", "RECON", f"{cid}: ditemukan POSISI HIDUP #{p['ticket']} — tidak dikirim ulang.")
            elif cid in deals:
                d = deals[cid]
                self.s.mark_intent(cid, state="RESOLVED", ticket=d["ticket"],
                                   fill_price=d["price"])
                self.log("INFO", "RECON", f"{cid}: order sudah dieksekusi & tertutup (#{d['ticket']}).")
            else:
                if it["state"] == "PENDING" and not it["sent_ts"]:
                    # mati sebelum sempat mengirim -> aman dibatalkan
                    self.s.mark_intent(cid, state="ABANDONED",
                                       last_error="mati sebelum order dikirim")
                    self.log("INFO", "RECON", f"{cid}: belum sempat terkirim — dibatalkan.")
                elif age_s < 90:
                    # mungkin masih diproses broker; jangan putuskan sekarang
                    self.s.mark_intent(cid, state="ORPHAN",
                                       last_error="menunggu kepastian broker")
                    self.log("WARN", "RECON", f"{cid}: belum jelas ({age_s:.0f}s) — ditunda.")
                    continue
                else:
                    self.s.mark_intent(cid, state="ABANDONED",
                                       last_error="tidak ditemukan di posisi maupun deal")
                    self.log("WARN", "RECON", f"{cid}: tidak ada jejak di MT5 — dianggap gagal.")

        still = self.s.unresolved_intents()
        self.frozen = bool(still)
        self.freeze_reason = f"{len(still)} intent masih menunggu" if still else ""
        if not still:
            self.log("INFO", "RECON", "Semua intent terselesaikan. Eksekusi aktif.")

    @staticmethod
    def _cid_from_comment(c):
        c = (c or "").strip()
        return c if c.startswith("MHF20-") else None

    # ------------------------------------------------------------------
    # GERBANG: semua alasan menolak entry
    # ------------------------------------------------------------------
    def _roll_day(self):
        d = datetime.now(timezone.utc).date()
        if d != self._day:
            self._day = d
            self.orders_today = 0

    def can_execute(self, ev, n_open, day_pnl, equity, peak):
        self._roll_day()
        c = self.cfg
        if not c.AUTO_EXECUTE:
            return False, "Auto-execute dimatikan (mode jurnal manual)"
        if self.frozen:
            return False, f"DIBEKUKAN: {self.freeze_reason}"
        if not HAVE_MT5:
            return False, "Paket MetaTrader5 tidak tersedia"
        if not self.b.connected:
            return False, "MT5 tidak terhubung"
        acc = self.b.account_snapshot() or {}
        if c.DEMO_ONLY and int(acc.get("trade_mode", 1)) == 0:
            return False, "AKUN REAL terdeteksi — DEMO_ONLY aktif, eksekusi diblokir"
        if not acc.get("trade_allowed", True):
            return False, "Trading tidak diizinkan terminal (AutoTrading mati?)"
        if getattr(c, "MAX_ENTRIES_PER_DAY", 0) > 0 and self.orders_today >= c.MAX_ENTRIES_PER_DAY:
            return False, (f"Batas {c.MAX_ENTRIES_PER_DAY} entry/hari sudah "
                           f"terpakai ({self.orders_today}). Menunggu besok.")
        if self.orders_today >= c.MAX_ORDERS_PER_DAY:
            return False, f"Batas {c.MAX_ORDERS_PER_DAY} order/hari tercapai"
        if n_open >= c.MAX_CONCURRENT:
            return False, f"Slot penuh ({n_open}/{c.MAX_CONCURRENT})"
        if day_pnl <= -c.DAILY_LOSS_LIMIT:
            return False, f"Limit rugi harian (${day_pnl:.2f})"
        if day_pnl >= c.DAILY_PROFIT_LIMIT:
            return False, f"Target profit harian tercapai (${day_pnl:.2f})"
        if peak > 0 and (equity / peak - 1) * 100 <= -c.KILL_SWITCH_DD_PCT:
            return False, "Kill-switch drawdown"
        if ev.spread > c.MAX_SPREAD_USD:
            return False, f"Spread ${ev.spread:.3f} > ${c.MAX_SPREAD_USD}"
        if self.s.intent_for_bar(self.b.symbol, ev.ts):
            return False, "Bar ini sudah punya order (anti-dobel)"
        free = float(acc.get("margin_free", 0) or 0)
        if free and free < c.MIN_FREE_MARGIN:
            return False, f"Margin bebas ${free:.0f} < ${c.MIN_FREE_MARGIN}"
        return True, ""

    # ------------------------------------------------------------------
    # KIRIM ORDER
    # ------------------------------------------------------------------
    def execute(self, ev, n_open, day_pnl, equity, peak):
        with self._lock:
            ok, why = self.can_execute(ev, n_open, day_pnl, equity, peak)
            if not ok:
                return dict(ok=False, reason=why)

            cid = f"MHF20-{ev.ts}-{uuid.uuid4().hex[:6]}"

            # --- LANGKAH 1: tulis intent & COMMIT sebelum menyentuh MT5 ---
            if self.s.create_intent(cid, ev.ts, self.b.symbol, "BUY",
                                    ev.lot, ev.sl, ev.tp2) is None:
                return dict(ok=False, reason="Bar ini sudah punya intent")
            self.log("INFO", "EXEC", f"Intent {cid} dicatat (lot {ev.lot} SL {ev.sl:.2f} TP {ev.tp2:.2f})")

            try:
                res = self._send(cid, ev)
            except Exception as e:
                # Tidak tahu order sampai atau tidak -> BEKUKAN, jangan tebak.
                self.s.mark_intent(cid, state="ORPHAN", last_error=f"exception: {e}")
                self.frozen = True
                self.freeze_reason = f"{cid} gagal dengan exception — perlu rekonsiliasi"
                self.log("ERROR", "EXEC", f"{cid} exception: {e} — eksekusi DIBEKUKAN.")
                return dict(ok=False, reason=str(e), frozen=True)
            return res

    def _send(self, cid, ev):
        c = self.cfg
        attempts = 0
        while attempts < c.MAX_SEND_ATTEMPTS:
            attempts += 1
            if not self.b.ensure():
                self.s.mark_intent(cid, attempts=attempts, last_error="MT5 tidak terhubung")
                time.sleep(1.0)
                continue

            tick = mt5.symbol_info_tick(self.b.symbol)
            info = mt5.symbol_info(self.b.symbol)
            if tick is None or info is None:
                self.s.mark_intent(cid, attempts=attempts, last_error="tick/info kosong")
                time.sleep(0.5)
                continue

            spread = tick.ask - tick.bid
            if spread > c.MAX_SPREAD_USD:
                self.s.mark_intent(cid, state="ABANDONED", attempts=attempts,
                                   last_error=f"spread melebar {spread:.3f}")
                return dict(ok=False, reason=f"Spread melebar jadi ${spread:.3f}")

            price = tick.ask
            digits = info.digits
            sl = round(price - c.SL_USD, digits)
            tp = round(price + c.TP2_R * c.SL_USD, digits)

            # hormati jarak stop minimum broker
            stop_lvl = (info.trade_stops_level or 0) * info.point
            if stop_lvl > 0:
                if price - sl < stop_lvl: sl = round(price - stop_lvl * 1.2, digits)
                if tp - price < stop_lvl: tp = round(price + stop_lvl * 1.2, digits)

            # Contract size broker bisa != 100 oz. Kalau beda, lot dari
            # signal_engine (yang memakai CONTRACT_SIZE=100) akan salah risiko.
            cs = float(getattr(info, 'trade_contract_size', c.CONTRACT_SIZE) or c.CONTRACT_SIZE)
            lot_req = ev.lot
            if abs(cs - c.CONTRACT_SIZE) > 1e-9:
                lot_req = ev.lot * (c.CONTRACT_SIZE / cs)
                self.log("WARN", "EXEC",
                         f"Contract size broker {cs} != {c.CONTRACT_SIZE}; lot dikoreksi "
                         f"{ev.lot} -> {lot_req:.2f} agar risiko tetap ${c.RISK_PER_POSITION}")
            lot = self._norm_lot(lot_req, info)
            if lot <= 0:
                self.s.mark_intent(cid, state="ABANDONED", last_error="lot tidak valid")
                return dict(ok=False, reason="Lot tidak valid")

            # deviation MT5 dalam POINT. Konversi dari USD sesuai digits simbol,
            # kalau tidak: digits=3 bikin toleransi 10x terlalu ketat -> requote.
            dev = max(1, int(round(c.MAX_SLIPPAGE_USD / info.point)))
            req = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.b.symbol,
                "volume": lot,
                "type": mt5.ORDER_TYPE_BUY,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": dev,
                "magic": MAGIC,
                "comment": cid,                      # identitas idempotensi
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": self._filling(info),
            }

            # --- LANGKAH 2: tandai SENT sebelum benar-benar mengirim ---
            self.s.mark_intent(cid, state="SENT", sent_ts=int(time.time() * 1000),
                               attempts=attempts, lot=lot, sl=sl, tp=tp)
            r = mt5.order_send(req)

            if r is None:
                err = mt5.last_error()
                self.s.mark_intent(cid, last_error=f"order_send None {err}")
                self.log("WARN", "EXEC", f"{cid} percobaan {attempts}: tidak ada balasan {err}")
                time.sleep(0.8)
                continue

            rc = int(r.retcode)
            self.s.mark_intent(cid, retcode=rc, comment=str(r.comment))

            if rc == mt5.TRADE_RETCODE_DONE:
                ticket = int(r.order or 0)
                pos = self._verify(cid, ticket)          # LANGKAH 3: verifikasi
                if pos:
                    self.s.mark_intent(cid, state="FILLED", ticket=pos["ticket"],
                                       fill_price=pos["price_open"])
                    self.s.upsert_trade(ticket=pos["ticket"], symbol=self.b.symbol,
                                        direction="BUY", entry_ts=pos["time"],
                                        entry_price=pos["price_open"], lot=pos["volume"],
                                        sl=pos["sl"], tp2=tp, status="OPEN", note=cid)
                    self.orders_today += 1
                    self.log("INFO", "EXEC",
                             f"TEREKSEKUSI #{pos['ticket']} {lot} lot @ {pos['price_open']:.2f} "
                             f"SL {pos['sl']:.2f} TP {tp:.2f}")
                    return dict(ok=True, ticket=pos["ticket"], price=pos["price_open"],
                                lot=lot, sl=sl, tp=tp, client_id=cid)
                # broker bilang DONE tapi posisi tak terlihat -> jangan tebak
                self.s.mark_intent(cid, state="ORPHAN",
                                   last_error="retcode DONE tapi posisi tidak ditemukan")
                self.frozen = True
                self.freeze_reason = f"{cid}: DONE tapi posisi tak terlihat"
                self.log("ERROR", "EXEC", f"{cid}: DONE tapi posisi tak terlihat — DIBEKUKAN.")
                return dict(ok=False, reason="Fill tidak terverifikasi", frozen=True)

            if rc in FATAL:
                self.s.mark_intent(cid, state="REJECTED",
                                   last_error=f"retcode {rc}: {r.comment}")
                self.log("WARN", "EXEC", f"{cid} DITOLAK retcode {rc}: {r.comment}")
                return dict(ok=False, reason=f"Ditolak broker ({rc}: {r.comment})")

            self.log("WARN", "EXEC", f"{cid} percobaan {attempts} retcode {rc}: {r.comment}")
            time.sleep(0.6 * attempts)

        self.s.mark_intent(cid, state="ORPHAN", last_error="kehabisan percobaan")
        self.frozen = True
        self.freeze_reason = f"{cid}: kehabisan percobaan, status tidak pasti"
        return dict(ok=False, reason="Kehabisan percobaan", frozen=True)

    def _verify(self, cid, ticket, tries=6):
        """Buktikan posisi benar-benar ada. Cocokkan lewat client_id, bukan asumsi."""
        for _ in range(tries):
            try:
                for p in self.b.positions():
                    if self._cid_from_comment(p.get("comment", "")) == cid:
                        return p
                    if ticket and p["ticket"] == ticket:
                        return p
            except Exception:
                pass
            time.sleep(0.4)
        return None

    @staticmethod
    def _norm_lot(lot, info):
        step = info.volume_step or 0.01
        lot = max(info.volume_min, min(info.volume_max, lot))
        return round(round(lot / step) * step, 2)

    @staticmethod
    def _filling(info):
        mode = info.filling_mode
        if mode & 1: return mt5.ORDER_FILLING_FOK
        if mode & 2: return mt5.ORDER_FILLING_IOC
        return mt5.ORDER_FILLING_RETURN

    # ------------------------------------------------------------------
    # MANAJEMEN POSISI: TP1 parsial + pindah ke break-even
    # ------------------------------------------------------------------
    def manage_positions(self):
        """Tutup 50% di 1R lalu geser SL ke BE+ — persis seperti backtest."""
        if not self.cfg.AUTO_EXECUTE or self.frozen or not HAVE_MT5:
            return
        c = self.cfg
        try:
            for p in self.b.positions():
                cid = self._cid_from_comment(p.get("comment", ""))
                if not cid:
                    continue                      # bukan posisi kita, jangan disentuh
                tick = mt5.symbol_info_tick(self.b.symbol)
                info = mt5.symbol_info(self.b.symbol)
                if not tick or not info:
                    return
                entry = p["price_open"]
                r1 = entry + c.TP1_R * c.SL_USD
                already_be = p["sl"] >= entry - 1e-6

                if tick.bid >= r1 and not already_be:
                    half = self._norm_lot(p["volume"] * c.TP1_CLOSE_PCT, info)
                    if 0 < half < p["volume"]:
                        cr = mt5.order_send({
                            "action": mt5.TRADE_ACTION_DEAL, "symbol": self.b.symbol,
                            "volume": half, "type": mt5.ORDER_TYPE_SELL,
                            "position": p["ticket"], "price": tick.bid,
                            "deviation": max(1, int(round(c.MAX_SLIPPAGE_USD / info.point))), "magic": MAGIC,
                            "comment": f"{cid}-TP1",
                            "type_time": mt5.ORDER_TIME_GTC,
                            "type_filling": self._filling(info)})
                        if cr and cr.retcode == mt5.TRADE_RETCODE_DONE:
                            self.log("INFO", "MANAGE",
                                     f"#{p['ticket']} TP1: {half} lot ditutup di {tick.bid:.2f}")
                    be = round(entry + (tick.ask - tick.bid), info.digits)
                    mr = mt5.order_send({
                        "action": mt5.TRADE_ACTION_SLTP, "symbol": self.b.symbol,
                        "position": p["ticket"], "sl": be, "tp": p["tp"], "magic": MAGIC})
                    if mr and mr.retcode == mt5.TRADE_RETCODE_DONE:
                        self.log("INFO", "MANAGE", f"#{p['ticket']} SL -> BE+ {be:.2f}")

                # time-stop 24 jam
                age_bars = (time.time() * 1000 - p["time"]) / 1000 / 60 / c.TIMEFRAME_MIN
                if age_bars >= c.TIME_STOP_BARS:
                    cr = mt5.order_send({
                        "action": mt5.TRADE_ACTION_DEAL, "symbol": self.b.symbol,
                        "volume": p["volume"], "type": mt5.ORDER_TYPE_SELL,
                        "position": p["ticket"], "price": tick.bid,
                        "deviation": max(1, int(round(c.MAX_SLIPPAGE_USD / info.point))), "magic": MAGIC,
                        "comment": f"{cid}-TIME", "type_time": mt5.ORDER_TIME_GTC,
                        "type_filling": self._filling(info)})
                    if cr and cr.retcode == mt5.TRADE_RETCODE_DONE:
                        self.log("INFO", "MANAGE", f"#{p['ticket']} ditutup oleh time-stop 24 jam")
        except Exception as e:
            self.log("WARN", "MANAGE", f"error: {e}")

    def panic_close_all(self):
        """Tombol darurat: tutup semua posisi milik MHF-20."""
        if not HAVE_MT5:
            return dict(ok=False, reason="MT5 tidak tersedia")
        n = 0
        try:
            info = mt5.symbol_info(self.b.symbol)
            for p in self.b.positions():
                if not self._cid_from_comment(p.get("comment", "")):
                    continue
                t = mt5.symbol_info_tick(self.b.symbol)
                r = mt5.order_send({
                    "action": mt5.TRADE_ACTION_DEAL, "symbol": self.b.symbol,
                    "volume": p["volume"], "type": mt5.ORDER_TYPE_SELL,
                    "position": p["ticket"], "price": t.bid,
                    "deviation": 100, "magic": MAGIC, "comment": "PANIC",
                    "type_time": mt5.ORDER_TIME_GTC, "type_filling": self._filling(info)})
                if r and r.retcode == mt5.TRADE_RETCODE_DONE:
                    n += 1
            self.log("WARN", "PANIC", f"{n} posisi ditutup manual oleh pengguna.")
            return dict(ok=True, closed=n)
        except Exception as e:
            return dict(ok=False, reason=str(e))
