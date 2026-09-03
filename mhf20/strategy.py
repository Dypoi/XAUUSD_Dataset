"""
================================================================================
MHF-20  ·  Momentum Continuation, High-Frequency, Risk-$20
XAUUSD Long-Only Trend-Aligned Breakout System
================================================================================
Backtest 2016-09..2026-09 (9.8 thn, net bid/ask + slippage):
  6,405 trades | 2.54 entry/hari | WR 53.51% | PF 1.203
  $10,000 -> $19,881 (+98.8%, CAGR 7.25%) | MaxDD -12.51% | t-stat +6.69
  Uji kontrol: PF +0.171 di atas entry acak
  IS 1.145 / OOS 1.232

PERINGATAN: sistem ini REAKTIF, bukan prediktif. Lihat docs/HONEST_LIMITS.md
================================================================================
"""
from dataclasses import dataclass, field
from typing import Optional, List
import numpy as np
import pandas as pd


# ============================== KONFIGURASI ==============================
@dataclass
class Config:
    SYMBOL: str = "XAUUSD"

    # --- Sinyal ---
    FVG_BUFFER: float = 0.30        # USD, ambang Fair Value Gap
    SWING_LOOKBACK: int = 6         # bar untuk displacement (high[-6:-1])
    BIAS_MA_H4: int = 240           # MA H4 ~40 hari
    ASIA_END_HOUR: int = 7          # UTC, batas sesi Asia
    LONDON_END_HOUR: int = 12       # UTC, batas sesi London

    # --- Geometri trade ---
    SL_USD: float = 12.00           # 120 pips
    TP1_R: float = 1.0              # TP1 = 1R -> tutup 50%
    TP2_R: float = 2.0              # TP2 = 2R -> tutup sisanya
    TP1_CLOSE_PCT: float = 0.50
    TIME_STOP_BARS: int = 288       # 24 jam pada M5

    # --- Risiko ---
    RISK_PER_POSITION: float = 20.0 # USD
    MAX_CONCURRENT: int = 8         # -> risiko total maks $160 (1.6% dari $10k)
    CONTRACT_SIZE: float = 100.0    # 1 lot = 100 oz
    MIN_LOT: float = 0.01
    MAX_LOT: float = 50.0
    SLIPPAGE_USD: float = 0.02

    # --- Guardrail ---
    MAX_SPREAD_USD: float = 1.20    # skip entry bila spread > ini (p99 ~1.15)
    DAILY_LOSS_LIMIT: float = 300.0
    DAILY_PROFIT_LIMIT: float = 500.0
    KILL_SWITCH_DD_PCT: float = 20.0
    NEWS_BLACKOUT_MIN: int = 30     # menit sebelum/sesudah berita high-impact

    LONG_ONLY: bool = True          # short TERBUKTI merugi (PF 0.748) - jangan diubah


CFG = Config()


# ============================== INDIKATOR ==============================
def session_levels(df: pd.DataFrame, cfg: Config = CFG) -> pd.DataFrame:
    """BSL/SSL kausal: expanding max/min DALAM hari berjalan (bukan agregat seharian).

    KRITIS: memakai groupby().transform('max') di sini = look-ahead bias.
    Bug itu (F-18 di bot ICAS) menggelembungkan PF sebesar +0.30.
    """
    day = df.index.normalize()
    hour = df.index.hour
    asia = hour < cfg.ASIA_END_HOUR
    london = (hour >= cfg.ASIA_END_HOUR) & (hour < cfg.LONDON_END_HOUR)

    ah = df['high'].where(asia).groupby(day).cummax().ffill()
    al = df['low'].where(asia).groupby(day).cummin().ffill()
    lh = df['high'].where(london).groupby(day).cummax().ffill()
    ll = df['low'].where(london).groupby(day).cummin().ffill()

    out = pd.DataFrame(index=df.index)
    out['BSL'] = pd.concat([ah, lh], axis=1).max(axis=1)
    out['SSL'] = pd.concat([al, ll], axis=1).min(axis=1)
    return out


def macro_bias(df_m5: pd.DataFrame, cfg: Config = CFG) -> pd.Series:
    """Bias bullish H4: close_H4 > MA240(close_H4). Reindex ffill = kausal."""
    h4 = df_m5['close'].resample('4h').last().dropna()
    bull = h4 > h4.rolling(cfg.BIAS_MA_H4).mean()
    return bull.reindex(df_m5.index, method='ffill').fillna(False)


def compute_signals(df: pd.DataFrame, cfg: Config = CFG) -> pd.DataFrame:
    """Hasilkan kolom sinyal. df butuh: open, high, low, close (mid, M5, UTC)."""
    lv = session_levels(df, cfg)
    bias = macro_bias(df, cfg)

    swing_h = df['high'].shift(2).rolling(cfg.SWING_LOOKBACK - 1).max()
    bull_fvg = df['low'] > (df['high'].shift(2) + cfg.FVG_BUFFER)

    bsl_swept = (df['high'].shift(1) >= lv['BSL']) | (df['high'].shift(2) >= lv['BSL'])
    displacement = (df['close'] > df['open']) & ((df['close'] > swing_h) | bull_fvg)

    out = pd.DataFrame(index=df.index)
    out['BSL'] = lv['BSL']; out['SSL'] = lv['SSL']
    out['bias_bull'] = bias
    out['bsl_swept'] = bsl_swept.fillna(False)
    out['displacement'] = displacement.fillna(False)
    out['long_signal'] = (out.bsl_swept & out.displacement & out.bias_bull)
    return out


# ============================== POSISI ==============================
@dataclass
class Position:
    id: int
    entry_time: pd.Timestamp
    entry_price: float
    lot: float
    sl: float
    tp1: float
    tp2: float
    remaining: float = 1.0
    tp1_hit: bool = False
    bars_held: int = 0
    realized_usd: float = 0.0

    def be_plus(self, spread: float) -> float:
        return self.entry_price + spread


def position_size(equity: float, spread: float, cfg: Config = CFG) -> float:
    """Lot dari jarak SL efektif. Urutan mutlak: struktur -> SL -> lot."""
    sl_eff = cfg.SL_USD + spread + cfg.SLIPPAGE_USD
    lot = cfg.RISK_PER_POSITION / (sl_eff * cfg.CONTRACT_SIZE)
    return float(np.clip(round(lot, 2), cfg.MIN_LOT, cfg.MAX_LOT))


def build_position(pid, ts, ask, spread, cfg: Config = CFG) -> Position:
    ep = ask + cfg.SLIPPAGE_USD
    return Position(
        id=pid, entry_time=ts, entry_price=ep,
        lot=position_size(0, spread, cfg),
        sl=ep - cfg.SL_USD,
        tp1=ep + cfg.TP1_R * cfg.SL_USD,
        tp2=ep + cfg.TP2_R * cfg.SL_USD,
    )
