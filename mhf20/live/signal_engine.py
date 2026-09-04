"""Mesin sinyal live MHF-20 — WAJIB identik dengan backtest.

Aturan anti-bug yang ditegakkan di sini:
  1. Sinyal HANYA dievaluasi pada bar M5 yang SUDAH TERTUTUP. Bar berjalan tidak pernah
     memicu entry (kalau tidak, itu look-ahead pada dirinya sendiri / repaint).
  2. BSL/SSL pakai cummax/cummin DALAM hari (bukan groupby max seharian).
  3. Bias H4 di-resample lalu ffill; wajib dropna sebelum rolling (celah akhir pekan
     menyuntik NaN dan membuat MA jadi NaN seluruhnya).
  4. Setiap syarat menghasilkan jejak alasan yang bisa dibaca manusia.
"""
import numpy as np, pandas as pd
from dataclasses import dataclass
from config import CFG


def build_frame(bars: list) -> pd.DataFrame:
    if not bars: return pd.DataFrame()
    df = pd.DataFrame(bars)
    df["timestamp"] = pd.to_datetime(df["ts"], unit="ms", utc=True).dt.tz_localize(None)
    return df.set_index("timestamp").sort_index()


def session_levels(df):
    day = df.index.normalize(); hour = df.index.hour
    asia = hour < CFG.ASIA_END_HOUR
    london = (hour >= CFG.ASIA_END_HOUR) & (hour < CFG.LONDON_END_HOUR)
    ah = df["high"].where(asia).groupby(day).cummax().ffill()
    al = df["low"].where(asia).groupby(day).cummin().ffill()
    lh = df["high"].where(london).groupby(day).cummax().ffill()
    ll = df["low"].where(london).groupby(day).cummin().ffill()
    return (pd.concat([ah, lh], axis=1).max(axis=1),
            pd.concat([al, ll], axis=1).min(axis=1))


def macro_bias(df):
    h4 = df["close"].resample("4h").last().dropna()      # dropna WAJIB
    if len(h4) < CFG.BIAS_MA_H4:
        return pd.Series(False, index=df.index), pd.Series(np.nan, index=df.index)
    ma = h4.rolling(CFG.BIAS_MA_H4).mean()
    bull = (h4 > ma).reindex(df.index, method="ffill").fillna(False)
    maf = ma.reindex(df.index, method="ffill")
    return bull, maf


@dataclass
class Evaluation:
    ts: int
    price: float
    spread: float
    passed: bool
    reasons: list
    blocked_by: str
    lot: float = 0.0
    sl: float = 0.0
    tp1: float = 0.0
    tp2: float = 0.0
    ctx: dict = None


def evaluate_closed_bar(df: pd.DataFrame, n_open_positions: int, day_pnl: float,
                        equity: float, peak_equity: float) -> Evaluation:
    """Evaluasi bar TERAKHIR YANG SUDAH TERTUTUP (df harus berakhir di bar tertutup)."""
    if len(df) < 300:
        return Evaluation(0, 0, 0, False, [], "WARMUP: data belum cukup", ctx={})

    BSL, SSL = session_levels(df)
    bull, ma_h4 = macro_bias(df)
    swing_h = df["high"].shift(2).rolling(CFG.SWING_LOOKBACK - 1).max()
    bull_fvg = df["low"] > (df["high"].shift(2) + CFG.FVG_BUFFER)

    i = len(df) - 1
    ts = int(df.index[i].value // 10**6)
    px = float(df["close"].iloc[i]); spr = float(df["spread"].iloc[i])
    hi1 = float(df["high"].iloc[i-1]); hi2 = float(df["high"].iloc[i-2])
    bsl = float(BSL.iloc[i]); sh = float(swing_h.iloc[i]) if pd.notna(swing_h.iloc[i]) else np.nan
    o = float(df["open"].iloc[i])

    c_sweep = (hi1 >= bsl) or (hi2 >= bsl)
    c_bull_candle = px > o
    c_break = (px > sh) if pd.notna(sh) else False
    c_fvg = bool(bull_fvg.iloc[i])
    c_disp = c_bull_candle and (c_break or c_fvg)
    c_bias = bool(bull.iloc[i])
    c_spread = spr <= CFG.MAX_SPREAD_USD
    c_slots = n_open_positions < CFG.MAX_CONCURRENT
    c_dayloss = day_pnl > -CFG.DAILY_LOSS_LIMIT
    c_dayprofit = day_pnl < CFG.DAILY_PROFIT_LIMIT
    dd = (equity / peak_equity - 1) * 100 if peak_equity > 0 else 0.0
    c_dd = dd > -CFG.KILL_SWITCH_DD_PCT

    R = [
        dict(grup="Sinyal", k="Sweep BSL", ok=bool(c_sweep),
             detail=f"high[-1]={hi1:.2f} / high[-2]={hi2:.2f} vs BSL={bsl:.2f}",
             why="Likuiditas sisi beli (high sesi Asia/London) harus sudah disapu."),
        dict(grup="Sinyal", k="Candle bullish", ok=bool(c_bull_candle),
             detail=f"close={px:.2f} > open={o:.2f}" if c_bull_candle else f"close={px:.2f} <= open={o:.2f}",
             why="Displacement harus datang dari candle naik."),
        dict(grup="Sinyal", k="Break swing / FVG", ok=bool(c_break or c_fvg),
             detail=f"break_swing={c_break} (swing={sh:.2f}) | FVG={c_fvg}" if pd.notna(sh) else f"FVG={c_fvg}",
             why="Bukti displacement: tembus swing pendek ATAU meninggalkan Fair Value Gap."),
        dict(grup="Filter", k="Bias H4 bullish", ok=bool(c_bias),
             detail=f"close_H4 vs MA240 = {'DI ATAS' if c_bias else 'DI BAWAH'}",
             why="Long-only searah tren menengah. Short terbukti rugi (PF 0,748)."),
        dict(grup="Guard", k=f"Spread <= ${CFG.MAX_SPREAD_USD}", ok=bool(c_spread),
             detail=f"spread=${spr:.3f}", why="Spread lebar memakan edge yang cuma +0,47pp."),
        dict(grup="Guard", k=f"Slot < {CFG.MAX_CONCURRENT}", ok=bool(c_slots),
             detail=f"posisi terbuka={n_open_positions}",
             why="Risiko total dikunci $160. 8x$80 pernah bikin DD -57%."),
        dict(grup="Guard", k="Limit rugi harian", ok=bool(c_dayloss),
             detail=f"PnL hari ini=${day_pnl:+.2f} (batas -${CFG.DAILY_LOSS_LIMIT})", why="Stop tilt."),
        dict(grup="Guard", k="Limit profit harian", ok=bool(c_dayprofit),
             detail=f"PnL hari ini=${day_pnl:+.2f} (batas +${CFG.DAILY_PROFIT_LIMIT})", why="Kunci hari bagus."),
        dict(grup="Guard", k="Kill-switch DD", ok=bool(c_dd),
             detail=f"DD={dd:.2f}% (batas -{CFG.KILL_SWITCH_DD_PCT}%)", why="Proteksi modal."),
    ]

    sig_ok = c_sweep and c_disp and c_bias
    guards_ok = c_spread and c_slots and c_dayloss and c_dayprofit and c_dd
    passed = sig_ok and guards_ok
    blocked = "" if passed else "; ".join(r["k"] for r in R if not r["ok"])

    sl_eff = CFG.SL_USD + spr + CFG.SLIPPAGE_USD
    lot = float(np.clip(round(CFG.RISK_PER_POSITION / (sl_eff * CFG.CONTRACT_SIZE), 2), 0.01, 50.0))
    ep = px + spr + CFG.SLIPPAGE_USD     # entry di ask
    ctx = dict(BSL=bsl, SSL=float(SSL.iloc[i]), swing_high=None if pd.isna(sh) else sh,
               ma_h4=None if pd.isna(ma_h4.iloc[i]) else float(ma_h4.iloc[i]),
               bias_bull=bool(c_bias), sig_ok=bool(sig_ok), guards_ok=bool(guards_ok),
               risk_usd=CFG.RISK_PER_POSITION, sl_eff=sl_eff)

    return Evaluation(ts=ts, price=px, spread=spr, passed=passed, reasons=R,
                      blocked_by=blocked, lot=lot, sl=ep - CFG.SL_USD,
                      tp1=ep + CFG.TP1_R * CFG.SL_USD, tp2=ep + CFG.TP2_R * CFG.SL_USD, ctx=ctx)
