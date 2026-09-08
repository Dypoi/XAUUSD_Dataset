"""
Strategi SMC usulan pengguna:
  trendline M5 -> order block -> 3 TOP -> CHOCH -> FVG -> BB -> ENTRY

SEMUA deteksi KAUSAL. Aturan yang dipegang:
  - Swing/fractal dikonfirmasi TERLAMBAT k bar (tidak boleh pakai bar masa depan).
  - Order block ditandai memakai shift POSITIF (bar lampau), bukan negatif.
  - Trendline diregresi dari jendela yang sudah tertutup.
  - Semua level dibandingkan dengan harga bar berjalan, entry di bar BERIKUTNYA.

"BB" ambigu -> diuji dua-duanya: Bollinger Bands dan Breaker Block.
"3 TOP" ambigu -> diuji triple-top ketat dan versi longgar (3 swing high beruntun).
"""
import numpy as np
import pandas as pd

K = 3            # bar konfirmasi fractal (delay wajib)
SWING_W = 5      # lebar fractal


def swings(df, w=SWING_W, k=K):
    """Fractal high/low, dikonfirmasi terlambat k bar (kausal)."""
    h, l = df['high'], df['low']
    is_h = (h == h.rolling(2 * w + 1, center=True).max())
    is_l = (l == l.rolling(2 * w + 1, center=True).min())
    # geser maju agar hanya diketahui setelah k bar -> tidak ada look-ahead
    return is_h.shift(w + k).fillna(False), is_l.shift(w + k).fillna(False)


def trendline_slope(close, win=60):
    """Kemiringan regresi linear pada jendela tertutup (bar lampau saja)."""
    x = np.arange(win)
    xm = x.mean()
    denom = ((x - xm) ** 2).sum()

    def f(y):
        return ((x - xm) * (y - y.mean())).sum() / denom

    return close.shift(1).rolling(win).apply(f, raw=True)


def build(df):
    """Hasilkan semua komponen sinyal."""
    o, h, l, c = df['open'], df['high'], df['low'], df['close']
    out = pd.DataFrame(index=df.index)

    # ---------- 1. TRENDLINE M5 ----------
    slope = trendline_slope(c, 60)
    out['trend_up'] = slope > 0

    # ---------- 2. ORDER BLOCK (bullish) ----------
    # candle bearish terakhir sebelum dorongan naik kuat. shift POSITIF = masa lalu.
    rng = (h - l).rolling(20).mean()
    bear = c < o
    push = (c.shift(1) > o.shift(1)) & ((c.shift(1) - o.shift(1)) > 0.8 * rng.shift(1))
    ob_bar = bear.shift(2) & push          # OB terjadi 2 bar lalu, dorongan 1 bar lalu
    ob_low = l.shift(2).where(ob_bar).ffill()
    ob_high = h.shift(2).where(ob_bar).ffill()
    out['ob_low'], out['ob_high'] = ob_low, ob_high
    # harga kembali menyentuh zona OB (mitigasi)
    out['ob_touch'] = (l <= ob_high) & (h >= ob_low) & ob_high.notna()

    # ---------- 3. "3 TOP" ----------
    sh, sl_ = swings(df)
    hi_val = h.shift(SWING_W + K).where(sh).ffill()
    # ambil TIGA swing high BERBEDA terakhir (bukan ffill dari nilai yang sama)
    only = h.shift(SWING_W + K).where(sh)          # NaN kecuali di bar swing
    seq = only.dropna()
    p1 = seq.reindex(df.index).ffill()
    p2 = seq.shift(1).reindex(df.index).ffill()
    p3 = seq.shift(2).reindex(df.index).ffill()
    tops = pd.concat([p1, p2, p3], axis=1)
    spread = (tops.max(axis=1) - tops.min(axis=1)) / tops.mean(axis=1) * 100
    out['top3_ketat'] = spread < 0.35
    # longgar: cukup ada 3 swing high tercatat
    out['top3_longgar'] = tops.notna().all(axis=1)
    out['res3'] = tops.mean(axis=1)

    # ---------- 4. CHOCH (change of character, bullish) ----------
    # harga menembus swing-high terakhir yang sudah terkonfirmasi
    last_sh = hi_val
    out['choch'] = (c > last_sh) & (c.shift(1) <= last_sh) & last_sh.notna()

    # ---------- 5. FVG (bullish fair value gap) ----------
    out['fvg'] = (l > h.shift(2)) & ((l - h.shift(2)) > 0.30)

    # ---------- 6a. BB = BOLLINGER BANDS ----------
    ma20 = c.rolling(20).mean()
    sd20 = c.rolling(20).std()
    out['bb_up'] = ma20 + 2 * sd20
    out['bb_squeeze'] = (4 * sd20 / ma20 * 100) < (4 * sd20 / ma20 * 100).rolling(100).quantile(0.35)
    out['bb_break'] = c > (ma20 + 2 * sd20)

    # ---------- 6b. BB = BREAKER BLOCK ----------
    # OB yang gagal (ditembus turun) lalu harga balik naik menembusnya kembali
    broke_dn = (c < ob_low) & ob_low.notna()
    broken_recent = broke_dn.rolling(48).max().astype(bool)
    out['breaker'] = broken_recent & (c > ob_high)

    return out
