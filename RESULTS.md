# Verification results — eth-pnl-fixed

Frozen dataset: `bars.csv`, 1,440 ETH/USDT 1-minute bars (24h ending
2026-11-13 12:17 UTC). Buy-and-hold over the window: **-3.36%**
(close 2028.68 -> 1960.59).

Commands run:

```
python3 strategy.py bars.csv > /tmp/pos.csv
python3 backtest.py /tmp/pos.csv
```

`positions.csv` was regenerated to `/tmp/pos.csv` and compared byte for byte:
**identical** (both SHA-256
`365417fa73c79bb239ee7a144430bdeaf9204beef68ecbd773db5ff572153545`).

## Full window

| metric | value |
|---|---|
| net PnL | **+3.17%** |
| gross PnL | +3.38% |
| costs | 0.21% |
| trades (position changes) | 2 |
| max drawdown | 2.38% |
| Sharpe (daily-scaled, sqrt(1440), not annualised) | 1.07 |
| time in market | 48.8% (702 / 1,440 bars) |

Positions are flat for the first 738 bars, short from bar 738 to 1,310, then
long from bar 1,311 to the end. There are only two transitions, both in the
second half of the window.

The previous Sharpe values were incorrect: the implementation subtracted the
previous *return* from cumulative PnL, instead of the previous cumulative PnL.
The corrected per-bar increments give 1.07 for the full window and 1.52 for the
second half. The sqrt(1440) scale is daily, not annual. These in-sample values
from one day and two transitions are not evidence of a reliable trading edge.
The local cost model is fixed taker plus slippage per unit turnover; it does
not reproduce an unpublished size-dependent official grader. The final open
position is marked to market, with no terminal liquidation fee.

## Half split

| window | net | gross | costs | trades | max DD | Sharpe |
|---|---|---|---|---|---|---|
| first half (bars 0-719) | 0.00% | 0.00% | 0.00% | 0 | 0.00% | 0.00 |
| second half (bars 720-1439) | +3.17% | +3.38% | 0.21% | 2 | 2.38% | 1.52 |

All of the result comes from the second half. During the first half price never
left the entry band, so the strategy stayed flat and paid nothing. This is a
single-regime sample: the headline number is one favourable trend, not an
average over many independent episodes.

## Cost sensitivity

From `backtest.py` (base = 5 bp taker + 2 bp slippage per side):

| scenario | net | max DD | trades |
|---|---|---|---|
| zero-cost (0 / 0) | +3.38% | 2.24% | 2 |
| base (5 bp + 2 bp) | +3.17% | 2.38% | 2 |
| 3x cost (15 bp + 6 bp) | +2.75% | 2.66% | 2 |

The strategy turns over twice, so total friction is 21 bp at base cost and
63 bp at 3x cost. Cost drag is small because the position is held for hundreds
of bars at a time; it is not because the signal is unusually accurate.

## Why this is a vol-normalised trend regime

The signal is the distance of price from a 240-bar simple moving average,
divided by the product of realised 1-minute return volatility, price and
`sqrt(240)`. That makes the threshold scale-free: `z = +0.5` means the same
fraction of a random-walk standard deviation whether ETH is at 1,000 or 5,000
and whether the day is quiet or turbulent. There are no fixed price levels,
clock rules or hardcoded dates, so the rule can in principle be applied
unchanged to another symbol or day, and thresholds do not need re-tuning when
the price level or volatility regime changes.

Hysteresis (`enter` at |z| > 0.5, `exit` only at |z| < 0.0) plus a six-flips-
per-hour cap deliberately trades little. Position changes cost two legs each,
so on a 1-minute series a signal that flips on noise is dominated by fees. The
volatility kill switch (flat when 60-bar vol exceeds 4x its trailing median)
avoids holding through blow-off moves.

## Why not over-fit to this single day

- This is one 24-hour sample, and the entire +3.17% comes from one trend in the
  second half. It is not out-of-sample evidence for the rule.
- The sample contains a single regime. A flat first half followed by one
  directional move gives one effective bet, not a distribution of outcomes; the
  Sharpe and drawdown figures have essentially no statistical power.
- The two-transition path means the result is highly sensitive to entry and
  exit timing. A few bars' difference in when the band was crossed would change
  the PnL materially.
- The parameters were selected by scanning neighbouring values in `research/`,
  so the published configuration sits on an in-sample plateau. A plateau is
  better than a single peak, but it is still selected on the same day it is
  scored on.
- To treat this as a real edge it needs testing on other days, other symbols
  and other volatility regimes, with the threshold fixed in advance. The
  honest conclusion from this window is that the implementation is
  cost-aware and internally consistent, not that the strategy has a proven
  positive expectancy.
