"""Backtest engine MHF-20 — bid/ask aware, multi-posisi, zero look-ahead."""
import numpy as np, pandas as pd
from strategy import Config, CFG, compute_signals


def run_backtest(df: pd.DataFrame, cfg: Config = CFG, equity0: float = 10_000.0,
                 verbose: bool = True) -> dict:
    """df kolom wajib: open,high,low,close (mid) + open_bid,open_ask,high_bid,low_bid,
    high_ask,low_ask,spread. Index UTC, M5."""
    sig = compute_signals(df, cfg)
    long_sig = sig['long_signal'].to_numpy()

    o_bid = df['open_bid'].to_numpy(); o_ask = df['open_ask'].to_numpy()
    h_bid = df['high_bid'].to_numpy(); l_bid = df['low_bid'].to_numpy()
    h_ask = df['high_ask'].to_numpy(); l_ask = df['low_ask'].to_numpy()
    spr = df['spread'].to_numpy()
    idx = df.index
    day = idx.normalize()

    equity = equity0
    peak = equity0
    open_pos = []          # list of dict
    closed = []
    pid = 0
    cur_day = None; day_pnl = 0.0
    halted = False

    for i in range(len(df) - 1):
        if day[i] != cur_day:
            cur_day = day[i]; day_pnl = 0.0

        # ---------- kelola posisi terbuka ----------
        still = []
        for p in open_pos:
            done = False; got = 0.0
            if l_bid[i] <= p['sl']:
                got = p['rem'] * ((p['sl'] - cfg.SLIPPAGE_USD) - p['ep']); done = True
                reason = 'SL' if not p['tp1'] else 'BE'
            else:
                if not p['tp1'] and h_bid[i] >= p['t1']:
                    got += cfg.TP1_CLOSE_PCT * (p['t1'] - p['ep'])
                    p['rem'] -= cfg.TP1_CLOSE_PCT
                    p['tp1'] = True
                    p['sl'] = p['ep'] + spr[i]           # BE+
                if p['tp1'] and h_bid[i] >= p['t2']:
                    got += p['rem'] * (p['t2'] - p['ep']); done = True; reason = 'TP2'
            p['bars'] += 1
            if not done and p['bars'] >= cfg.TIME_STOP_BARS:
                mp = (h_bid[i] + l_bid[i]) / 2
                got += p['rem'] * (mp - p['ep']); done = True; reason = 'TIME'
            if got != 0.0:
                usd = got * p['lot'] * cfg.CONTRACT_SIZE
                equity += usd; day_pnl += usd; p['acc'] += usd
            if done:
                closed.append(dict(id=p['id'], entry_time=idx[p['i']], exit_time=idx[i],
                                   entry=p['ep'], lot=p['lot'], pnl=p['acc'],
                                   bars=p['bars'], reason=reason, equity=equity))
            else:
                still.append(p)
        open_pos = still

        peak = max(peak, equity)
        if (equity / peak - 1) * 100 <= -cfg.KILL_SWITCH_DD_PCT:
            halted = True
        if halted or equity <= 0:
            continue

        # ---------- entry baru ----------
        if not long_sig[i]:
            continue
        if len(open_pos) >= cfg.MAX_CONCURRENT:
            continue
        if day_pnl <= -cfg.DAILY_LOSS_LIMIT or day_pnl >= cfg.DAILY_PROFIT_LIMIT:
            continue
        j = i + 1
        spread = o_ask[j] - o_bid[j]
        if spread > cfg.MAX_SPREAD_USD:
            continue
        sl_eff = cfg.SL_USD + spread + cfg.SLIPPAGE_USD
        lot = float(np.clip(round(cfg.RISK_PER_POSITION / (sl_eff * cfg.CONTRACT_SIZE), 2),
                            cfg.MIN_LOT, cfg.MAX_LOT))
        ep = o_ask[j] + cfg.SLIPPAGE_USD
        pid += 1
        open_pos.append(dict(id=pid, i=j, ep=ep, lot=lot,
                             sl=ep - cfg.SL_USD, t1=ep + cfg.TP1_R * cfg.SL_USD,
                             t2=ep + cfg.TP2_R * cfg.SL_USD, rem=1.0, tp1=False,
                             bars=0, acc=0.0))

    tr = pd.DataFrame(closed)
    if tr.empty:
        return dict(trades=tr, stats={})
    tr = tr.sort_values('exit_time').reset_index(drop=True)
    p = tr.pnl.to_numpy()
    eq = pd.Series(tr.equity.to_numpy(), index=pd.DatetimeIndex(tr.exit_time))
    yrs = (tr.exit_time.iloc[-1] - tr.entry_time.iloc[0]).days / 365.25
    gp, gl = p[p > 0].sum(), -p[p < 0].sum()
    nb = 252 * yrs
    stats = dict(
        trades=len(p), win_rate=(p > 0).mean() * 100,
        profit_factor=gp / max(gl, 1e-9), net=p.sum(),
        final_equity=eq.iloc[-1], total_return_pct=(eq.iloc[-1] / equity0 - 1) * 100,
        cagr_pct=((eq.iloc[-1] / equity0) ** (1 / yrs) - 1) * 100,
        max_dd_pct=(eq / eq.cummax() - 1).min() * 100,
        entries_per_day=len(p) / nb, years=yrs,
        expectancy=p.mean(), expectancy_R=p.mean() / cfg.RISK_PER_POSITION,
        t_stat=p.mean() / (p.std(ddof=1) / np.sqrt(len(p))),
        avg_win=p[p > 0].mean(), avg_loss=p[p < 0].mean(),
        halted=halted,
    )
    if verbose:
        print(f"{'Trades':22s}: {stats['trades']:,}")
        print(f"{'Entry/hari':22s}: {stats['entries_per_day']:.2f}")
        print(f"{'Win rate':22s}: {stats['win_rate']:.2f}%")
        print(f"{'Profit Factor':22s}: {stats['profit_factor']:.3f}")
        print(f"{'Equity akhir':22s}: ${stats['final_equity']:,.0f}  ({stats['total_return_pct']:+.1f}%)")
        print(f"{'CAGR':22s}: {stats['cagr_pct']:.2f}%")
        print(f"{'Max Drawdown':22s}: {stats['max_dd_pct']:.2f}%")
        print(f"{'Ekspektasi/trade':22s}: ${stats['expectancy']:+.2f}  ({stats['expectancy_R']:+.3f}R)")
        print(f"{'t-stat':22s}: {stats['t_stat']:+.2f}")
    return dict(trades=tr, stats=stats, equity=eq, signals=sig)
