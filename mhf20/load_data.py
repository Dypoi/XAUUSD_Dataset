"""Loader dataset XAUUSD M1 -> M5 bid/ask."""
import pandas as pd, numpy as np, glob

def load_m5(parquet_cache='/home/user/XAUUSD_Dataset/research/m1.parquet',
            csv_glob='/home/user/XAUUSD_Dataset/XAUUSD_M1_*.csv'):
    try:
        d = pd.read_parquet(parquet_cache)
        d = d.set_index('timestamp') if 'timestamp' in d.columns else d
    except Exception:
        dfs = [pd.read_csv(f, parse_dates=['timestamp']) for f in sorted(glob.glob(csv_glob))]
        d = pd.concat(dfs).sort_values('timestamp').drop_duplicates('timestamp').set_index('timestamp')
    d = d.sort_index()
    mid_o = (d.open_bid + d.open_ask) / 2; mid_h = (d.high_bid + d.high_ask) / 2
    mid_l = (d.low_bid + d.low_ask) / 2;  mid_c = (d.close_bid + d.close_ask) / 2
    m5 = pd.DataFrame({
        'open': mid_o.resample('5min').first(), 'high': mid_h.resample('5min').max(),
        'low': mid_l.resample('5min').min(),   'close': mid_c.resample('5min').last(),
        'open_bid': d.open_bid.resample('5min').first(), 'open_ask': d.open_ask.resample('5min').first(),
        'high_bid': d.high_bid.resample('5min').max(),  'low_bid': d.low_bid.resample('5min').min(),
        'high_ask': d.high_ask.resample('5min').max(),  'low_ask': d.low_ask.resample('5min').min(),
        'spread': (d.close_ask - d.close_bid).resample('5min').median(),
    }).dropna()
    return m5
