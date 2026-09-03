"""
XAU-TRV : Gold Trend-Regime Vol-Targeted System (4H)
====================================================
Signal  : ensemble of 3 vol-normalised momentum horizons (20d/40d/120d) on 4H mid bars
Gate    : stay invested unless ensemble < -0.35 (bear regime) -> cut to 25% floor
Sizing  : inverse-vol, 10% annual vol target, leverage cap 3x
Costs   : half bid/ask spread per side (from actual dataset quotes) + 0.5bp slip/comm
Execution: signal computed at 4H close, position applied from NEXT bar (no look-ahead)
"""
import pandas as pd, numpy as np, json, os

RESEARCH = os.path.dirname(os.path.abspath(__file__))
P = dict(n1=120, n2=240, n3=720, thresh=-0.35, floor=0.25,
         vol_target=0.10, lev_cap=3.0, vol_lb=500, rv_lb=480, slip_bps=0.5)

def load_bars(rule='4h'):
    d = pd.read_parquet(f'{RESEARCH}/m1.parquet').set_index('timestamp').sort_index()
    mid = (d.close_bid + d.close_ask) / 2
    spread = (d.close_ask - d.close_bid)
    b = pd.DataFrame({'o': mid.resample(rule).first(), 'h': mid.resample(rule).max(),
                      'l': mid.resample(rule).min(), 'c': mid.resample(rule).last(),
                      'spread': spread.resample(rule).median()}).dropna()
    b['ret'] = np.log(b.c).diff()
    b['cost_bps'] = (b.spread / b.c * 1e4) / 2 + P['slip_bps']
    return b

def signal(b):
    c = np.log(b.c); v = b.ret.rolling(P['vol_lb']).std()
    zs = [(c - c.shift(n)) / (v * np.sqrt(n)) for n in (P['n1'], P['n2'], P['n3'])]
    ens = sum(np.tanh(z) for z in zs) / 3
    raw = P['floor'] + (1 - P['floor']) * (ens > P['thresh']).astype(float)
    return ens, raw

def backtest(b, raw, bpy=6*252, vol_target=None, cap=None):
    vt = vol_target or P['vol_target']; cp = cap or P['lev_cap']
    rv = b.ret.rolling(P['rv_lb']).std() * np.sqrt(bpy)
    lev = (vt / rv).clip(0, cp)
    expo = (raw * lev).shift(1).fillna(0)          # decided at t-1 close, held over t
    gross = expo * b.ret
    turn = expo.diff().abs().fillna(0)
    cost = turn * b.cost_bps / 1e4
    net = (gross - cost).fillna(0)
    out = pd.DataFrame({'ret': b.ret, 'expo': expo, 'gross': gross,
                        'cost': cost, 'net': net})
    out['equity'] = (1 + out.net).cumprod()
    return out

def stats(r, bpy=6*252, label=''):
    n = r.net
    eq = (1 + n).cumprod()
    yrs = (r.index[-1] - r.index[0]).days / 365.25
    cagr = eq.iloc[-1] ** (1 / yrs) - 1
    vol = n.std() * np.sqrt(bpy)
    dd = eq / eq.cummax() - 1
    daily = eq.resample('D').last().ffill().pct_change().dropna()
    dn = daily[daily < 0]
    return {
        'label': label, 'years': round(yrs, 2),
        'total_return_pct': round((eq.iloc[-1] - 1) * 100, 2),
        'cagr_pct': round(cagr * 100, 2), 'vol_ann_pct': round(vol * 100, 2),
        'sharpe': round(n.mean() * bpy / vol, 3) if vol else 0,
        'sortino': round(daily.mean() / dn.std() * np.sqrt(252), 3) if len(dn) > 1 else None,
        'max_dd_pct': round(dd.min() * 100, 2),
        'calmar': round(cagr / abs(dd.min()), 3) if dd.min() < 0 else None,
        'longest_dd_days': int(_longest_dd(eq)),
        'hit_rate_days_pct': round((daily > 0).mean() * 100, 2),
        'avg_exposure': round(r.expo.mean(), 3),
        'max_exposure': round(r.expo.max(), 3),
        'time_invested_pct': round((r.expo > 0.01).mean() * 100, 2),
        'gross_cagr_pct': round((((1 + r.gross).cumprod().iloc[-1]) ** (1 / yrs) - 1) * 100, 2),
        'cost_drag_pct_yr': round(r.cost.sum() / yrs * 100, 3),
        'turnover_x_yr': round(r.expo.diff().abs().sum() / yrs, 1),
        'skew': round(daily.skew(), 2), 'kurtosis': round(daily.kurtosis(), 2),
        'var95_daily_pct': round(np.percentile(daily, 5) * 100, 2),
        'cvar95_daily_pct': round(daily[daily <= np.percentile(daily, 5)].mean() * 100, 2),
    }

def _longest_dd(eq):
    peak = eq.cummax(); under = eq < peak * 0.9999
    best = cur = 0; start = None
    for t, u in under.items():
        if u:
            start = start or t; cur = (t - start).days
            best = max(best, cur)
        else:
            start = None
    return best
