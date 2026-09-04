"""Server dashboard MHF-20. Jalan lokal, tanpa dependensi internet."""
import sys, os, json, asyncio, signal as sigmod, time
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [_HERE, os.path.dirname(_HERE)]

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from config import CFG, as_dict
from store import Store, now_ms
from runner import Runner

app = FastAPI(title="MHF-20 Journal")
app.mount("/static", StaticFiles(directory=os.path.join(_HERE, "static")), name="static")

STORE = Store(CFG.DB_PATH)
BRIDGE = None
RUN = None


def build_bridge():
    global BRIDGE
    mode = os.environ.get("MHF20_MODE", "mt5").lower()
    logf = lambda l, k, m, p=None: STORE.log(l, k, m, p)
    if mode == "replay":
        from mt5_bridge import ReplayBridge
        cache = os.path.join(_HERE, "cache", "m5.parquet")
        BRIDGE = ReplayBridge(cache, logger=logf)
        print(">> MODE REPLAY (tanpa MT5)")
    else:
        from mt5_bridge import MT5Bridge
        BRIDGE = MT5Bridge(CFG.SYMBOL, logger=logf)
        if not BRIDGE.connect():
            print(">> MT5 belum siap. Runner akan terus mencoba menyambung.")
    return BRIDGE


@app.on_event("startup")
def _startup():
    global RUN
    b = build_bridge()
    RUN = Runner(b, STORE)
    RUN.start()


@app.on_event("shutdown")
def _shutdown():
    if RUN: RUN.stop()


@app.get("/", response_class=HTMLResponse)
def index():
    with open(os.path.join(_HERE, "static", "index.html"), encoding="utf-8") as f:
        return f.read()


@app.get("/api/state")
def api_state():
    st = dict(RUN.state) if RUN else {}
    st["config"] = as_dict()
    st["symbol"] = BRIDGE.symbol if BRIDGE else "?"
    hb = STORE.last_beat("main")
    st["heartbeat_age_s"] = (now_ms() - hb["ts"]) / 1000 if hb else None
    st.pop("current_bar", None)
    return JSONResponse(st)


@app.get("/api/bars")
def api_bars(limit: int = 500):
    rows = STORE.bars(BRIDGE.symbol if BRIDGE else CFG.SYMBOL, limit)
    cur = RUN.state.get("current_bar") if RUN else None
    return dict(bars=rows, current=cur)


@app.get("/api/signals")
def api_signals(limit: int = 100, only_passed: int = 0):
    return dict(signals=STORE.signals(limit, bool(only_passed)))


@app.post("/api/panic")
def api_panic():
    """Tombol darurat: tutup semua posisi MHF-20."""
    if not RUN: return dict(ok=False, reason="belum siap")
    r = RUN.ex.panic_close_all()
    STORE.log("WARN", "PANIC", f"Panic close dipicu: {r}")
    return r


@app.post("/api/toggle_auto")
def api_toggle():
    """Hidup/matikan auto-execute saat berjalan."""
    CFG.AUTO_EXECUTE = not CFG.AUTO_EXECUTE
    STORE.log("WARN", "CONFIG", f"AUTO_EXECUTE -> {CFG.AUTO_EXECUTE}")
    return dict(auto_execute=CFG.AUTO_EXECUTE)


@app.post("/api/unfreeze")
def api_unfreeze():
    """Paksa rekonsiliasi ulang setelah pembekuan."""
    if not RUN: return dict(ok=False)
    RUN.ex.reconcile_intents()
    return dict(frozen=RUN.ex.frozen, reason=RUN.ex.freeze_reason)


@app.get("/api/intents")
def api_intents(limit: int = 100):
    return dict(intents=STORE.intents(limit))


@app.get("/api/trades")
def api_trades(limit: int = 200):
    return dict(trades=STORE.trades(limit))


@app.get("/api/events")
def api_events(limit: int = 200):
    return dict(events=STORE.events(limit))


@app.post("/api/note/{trade_id}")
async def api_note(trade_id: int, payload: dict):
    with STORE.tx() as cx:
        cx.execute("UPDATE trades SET note=? WHERE id=?", (payload.get("note", ""), trade_id))
    return dict(ok=True)


@app.get("/api/report")
def api_report():
    """Ringkasan jurnal 5 hari."""
    tr = [t for t in STORE.trades(1000) if t["status"] == "CLOSED" and t["pnl"] is not None]
    sg = STORE.signals(2000)
    n = len(tr); wins = [t for t in tr if t["pnl"] > 0]
    gp = sum(t["pnl"] for t in wins); gl = -sum(t["pnl"] for t in tr if t["pnl"] <= 0)
    j = STORE.sget("journal", {})
    return dict(
        journal_day=(RUN.state.get("journal_day") if RUN else 1),
        journal_days_total=CFG.JOURNAL_DAYS,
        start_equity=j.get("start_equity"),
        trades=n, wins=len(wins),
        win_rate=(100 * len(wins) / n) if n else 0,
        gross_profit=gp, gross_loss=gl,
        profit_factor=(gp / gl) if gl > 0 else None,
        net=sum(t["pnl"] for t in tr),
        expectancy=(sum(t["pnl"] for t in tr) / n) if n else 0,
        expectancy_R=(sum(t["pnl"] for t in tr) / n / CFG.RISK_PER_POSITION) if n else 0,
        signals_total=len(sg), signals_passed=sum(1 for s in sg if s["passed"]),
        signals_blocked=sum(1 for s in sg if not s["passed"]),
    )


@app.get("/api/export")
def api_export():
    return dict(trades=STORE.trades(5000), signals=STORE.signals(5000),
                events=STORE.events(2000), report=api_report())


@app.websocket("/ws")
async def ws(sock: WebSocket):
    await sock.accept()
    try:
        while True:
            st = dict(RUN.state) if RUN else {}
            cur = st.pop("current_bar", None)
            hb = STORE.last_beat("main")
            payload = dict(
                type="state", ts=now_ms(),
                status=st.get("status"), mt5=st.get("mt5"),
                tick=st.get("tick"), equity=st.get("equity"), peak=st.get("peak"),
                day_pnl=st.get("day_pnl"), account=st.get("account"),
                open_positions=st.get("open_positions"), journal_day=st.get("journal_day"),
                last_eval=st.get("last_eval"), errors=st.get("errors"),
                frozen=st.get("frozen"), freeze_reason=st.get("freeze_reason"),
                auto_execute=CFG.AUTO_EXECUTE, orders_today=st.get("orders_today", 0),
                last_exec=st.get("last_exec"),
                current_bar=cur, symbol=BRIDGE.symbol if BRIDGE else "?",
                heartbeat_age_s=((now_ms() - hb["ts"]) / 1000 if hb else None),
                uptime_s=(now_ms() - st.get("uptime_start", now_ms())) / 1000,
            )
            await sock.send_text(json.dumps(payload, default=str))
            await asyncio.sleep(CFG.WS_PUSH_MS / 1000)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass


def main():
    host = os.environ.get("MHF20_HOST", CFG.HOST)
    port = int(os.environ.get("MHF20_PORT", CFG.PORT))
    print(f"\n  MHF-20 Journal  ->  http://{host}:{port}\n  Ctrl+C untuk berhenti (state tersimpan otomatis)\n")
    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    main()
