import numpy as np, pandas as pd
from engine import run

DATA='/home/user/XAUUSD_Dataset/research/m1.parquet'

def load():
    d=pd.read_parquet(DATA).set_index('timestamp').sort_index()
    return d

def build_m5(d):
    mid=(d.close_bid+d.close_ask)/2
    m5=pd.DataFrame({
        'o':mid.resample('5min').first(),'h':mid.resample('5min').max(),
        'l':mid.resample('5min').min(),'c':mid.resample('5min').last(),
        'n':mid.resample('5min').count()}).dropna()
    m5=m5[m5.n>=3]
    return m5

def signals(m5, lb=48, z_th=2.5, atr_n=48, hour_lo=0, hour_hi=7,
            trend_n=288, trend_filter=True, rsi_gate=True):
    c=m5.c
    ma=c.rolling(lb).mean(); sd=c.rolling(lb).std()
    z=(c-ma)/sd
    atr=(m5.h-m5.l).rolling(atr_n).mean()
    hour=c.index.hour
    sess=(hour>=hour_lo)&(hour<hour_hi)
    # trend filter: only fade when not in strong daily trend against us
    slope=(c-c.shift(trend_n))/ (atr*np.sqrt(trend_n))
    long_ok=(z<-z_th)&sess
    short_ok=(z>z_th)&sess
    if trend_filter:
        long_ok&= (slope>-1.5); short_ok&=(slope<1.5)
    # require stabilisation: last bar reverting
    if rsi_gate:
        long_ok &= (c>m5.o); short_ok &= (c<m5.o)
    sig=pd.Series(0,index=c.index)
    sig[long_ok.fillna(False)]=1
    sig[short_ok.fillna(False)]=-1
    sig[(long_ok&short_ok).fillna(False)]=0
    out=pd.DataFrame({'sig':sig,'atr':atr,'z':z})
    return out.dropna()

def backtest(d, sg, tp_mult=1.0, sl_mult=1.0, max_bars_m1=240,
             comm_usd=0.10, slip=0.02):
    """Trade at the M1 bar OPEN following the M5 signal-bar close.
    comm_usd/slip are per ounce; longs buy at ask, sell at bid."""
    m1idx = d.index
    s = sg[sg.sig != 0]
    entry_ts = s.index + pd.Timedelta(minutes=5)          # M5 close = decision time
    pos = m1idx.searchsorted(entry_ts)
    ok = pos < len(m1idx) - 1
    pos = pos[ok].astype(np.int64)
    side = s.sig.values[ok].astype(np.int64)
    atr = s.atr.values[ok]
    keep, e_t, x_t, e_p, x_p, pnl, rs = run(
        pos, side, atr * tp_mult, atr * sl_mult, max_bars_m1,
        d.high_bid.values, d.low_bid.values, d.close_bid.values,
        d.high_ask.values, d.low_ask.values, d.close_ask.values,
        d.open_bid.values, d.open_ask.values, comm_usd, 1, slip)
    tr = pd.DataFrame({
        'entry_time': m1idx[e_t], 'exit_time': m1idx[x_t],
        'side': side[keep], 'entry': e_p, 'exit': x_p,
        'atr': atr[keep], 'pnl_usd_per_oz': pnl,
        'reason': pd.Categorical.from_codes(rs - 1, ['SL', 'TP', 'TIME']),
        'bars': x_t - e_t})
    tr['ret_bps'] = tr.pnl_usd_per_oz / tr.entry * 1e4
    return tr


def metrics(tr, risk_per_trade=0.01, equity0=10000.0, sl_mult=1.0):
    r = tr.pnl_usd_per_oz.values
    out = {}
    n = len(r)
    out['trades'] = n
    out['win_rate'] = float((r > 0).mean())
    out['avg_usd_per_oz'] = float(r.mean())
    out['total_usd_per_oz'] = float(r.sum())
    gp, gl = r[r > 0].sum(), -r[r < 0].sum()
    out['profit_factor'] = float(gp / gl) if gl > 0 else float('inf')
    out['payoff'] = float(r[r > 0].mean() / abs(r[r < 0].mean())) if (r < 0).any() else float('inf')
    out['t_stat'] = float(r.mean() / (r.std(ddof=1) / np.sqrt(n))) if n > 1 else 0.0
    # R-multiples: risk = sl_mult*ATR
    R = r / (tr.atr.values * sl_mult)
    out['avg_R'] = float(R.mean()); out['R_std'] = float(R.std())
    out['expectancy_R'] = float(R.mean())
    # compounded equity with fixed fractional risk
    eq = equity0 * np.cumprod(1 + risk_per_trade * R)
    out['final_equity'] = float(eq[-1])
    dd = eq / np.maximum.accumulate(eq) - 1
    out['max_dd_pct'] = float(dd.min() * 100)
    yrs = (tr.exit_time.iloc[-1] - tr.entry_time.iloc[0]).days / 365.25
    out['years'] = float(yrs)
    out['cagr_pct'] = float(((eq[-1] / equity0) ** (1 / yrs) - 1) * 100)
    out['calmar'] = float(out['cagr_pct'] / abs(out['max_dd_pct'])) if out['max_dd_pct'] < 0 else float('inf')
    # daily-return Sharpe on R-equity
    dr = pd.Series(eq, index=pd.DatetimeIndex(tr.exit_time)).resample('D').last().ffill().pct_change().dropna()
    out['sharpe_daily'] = float(dr.mean() / dr.std() * np.sqrt(252)) if dr.std() > 0 else 0.0
    dn = dr[dr < 0]
    out['sortino'] = float(dr.mean() / dn.std() * np.sqrt(252)) if len(dn) > 1 else float('inf')
    out['trades_per_year'] = float(n / yrs)
    out['avg_bars_held'] = float(tr.bars.mean())
    out['pct_tp'] = float((tr.reason == 'TP').mean())
    out['pct_sl'] = float((tr.reason == 'SL').mean())
    out['pct_time'] = float((tr.reason == 'TIME').mean())
    out['equity'] = eq
    return out
