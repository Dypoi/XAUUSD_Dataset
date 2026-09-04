"""Konfigurasi jurnal live MHF-20. SATU sumber kebenaran."""
import os, sys
from dataclasses import dataclass, asdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@dataclass
class LiveConfig:
    SYMBOL: str = "XAUUSDm"        # Exness sering pakai suffix 'm'. Auto-resolve saat start.
    TIMEFRAME_MIN: int = 5
    JOURNAL_DAYS: int = 5

    # --- Geometri (WAJIB identik dengan backtest) ---
    SL_USD: float = 12.0
    TP1_R: float = 1.0
    TP2_R: float = 2.0
    TP1_CLOSE_PCT: float = 0.50
    TIME_STOP_BARS: int = 288
    RISK_PER_POSITION: float = 20.0
    MAX_CONCURRENT: int = 8
    CONTRACT_SIZE: float = 100.0
    SLIPPAGE_USD: float = 0.02

    # --- Sinyal ---
    FVG_BUFFER: float = 0.30
    SWING_LOOKBACK: int = 6
    BIAS_MA_H4: int = 240
    ASIA_END_HOUR: int = 7
    LONDON_END_HOUR: int = 12
    MAX_SPREAD_USD: float = 1.20

    # --- Guardrail ---
    DAILY_LOSS_LIMIT: float = 300.0
    DAILY_PROFIT_LIMIT: float = 500.0
    KILL_SWITCH_DD_PCT: float = 20.0

    # --- Runtime ---
    TICK_POLL_MS: int = 250          # polling MT5 (dashboard update ~per detik)
    WS_PUSH_MS: int = 500
    WARMUP_BARS: int = 26000        # >= 240 bar H4 (11.520 M5) + margin. KURANG DARI INI = bias H4 selalu False.
    HOST: str = "127.0.0.1"
    PORT: int = 8765
    DB_PATH: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "journal.db")
    HEARTBEAT_SEC: int = 5
    STALE_TICK_SEC: int = 20         # tidak ada tick selama ini -> status DEGRADED

    ALERT_SOUND: bool = True
    READ_ONLY: bool = True           # TIDAK PERNAH kirim order. Jangan diubah.

CFG = LiveConfig()
def as_dict(): return asdict(CFG)
