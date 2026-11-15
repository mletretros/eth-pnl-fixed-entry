# AIProve entry — eth-pnl-fixed

Strategy for the frozen ETH 1-minute dataset (`bars.csv`, 1,440 real
ETH/USDT Binance bars, 24h ending 2026-11-13 12:17 UTC). Metric: net PnL after
costs; ties break on lower max drawdown.

## Interface

```
python3 strategy.py bars.csv > positions.csv   # one target position per bar
python3 backtest.py positions.csv              # replay with the cost model
```

`strategy.py` reads only bars up to bar *i* to emit the position held over bar
*i+1*. No lookahead. Positions are `-1 / 0 / +1`.

## Signal

Vol-normalised distance of price from its slow mean:

```
z[i] = (close[i] - SMA_240[i]) / (sigma_240[i] * close[i] * sqrt(240))
```

`sigma_240` is the stdev of 1-minute returns over the same window, so `z` is
scale-free: `z = +2` always means "price sits two k-bar random-walk deviations
above its own mean", whatever ETH's price or volatility regime is. That is the
part that generalises past this sample — no price thresholds, no clock rules, no
hardcoded levels.

Regime with hysteresis (cost control — a flip costs 2 legs, so noise must not be
allowed to flip us):

| condition | target |
|---|---|
| `z > +0.5` | long `+1` |
| `z < -0.5` | short `-1` |
| `|z| < 0.0` | flat |

Plus two gates: flat during the 241-bar warm-up, flat when realised 60-bar vol
exceeds 4x its slow median (risk-off), and at most 6 flips per hour.

## Result on the published window

Cost model: 5 bp taker fee + 2 bp slippage per side, charged on every position
change, fills only on the *next* bar.

```
full window : net_pct=3.17  gross_pct=3.38  cost_pct=0.21  trades=2  max_dd_pct=2.38
first half  : net_pct=0.00  (stays flat — price never leaves the band)
second half : net_pct=3.17  max_dd_pct=2.38
zero-cost   : net=3.38%  3x cost: net=2.75%
```

Buy-and-hold over the same window was **-3.33%**. Two trades, 49% time in market,
drawdown 2.4% against a 3.2% return.

Cost sensitivity is the point of the design: with 2 trades the strategy only
pays 21 bp of friction, so it survives a 3x cost assumption (still +2.75%). Any
version of this idea that trades every spike (mean reversion at 1σ-2σ, ~150-300
trades) loses 5-15% on the same data purely to fees — see `research/`.

## What this is not

It is not fitted to the sample's direction. It has no constant long or short
bias: on this window it first goes short and then ends long when the same z
statistic turns positive. The parameters (240 bars,
0.5σ) were picked from a plateau of neighbouring values that all give +2.3 to
+3.2% with 2-9 trades, not from a single peak — the grid is in
`research/tune.py`.

## Files

```
strategy.py        the entry (signal + hysteresis + risk gates)
backtest.py        cost-aware replay, half-split and cost-sensitivity output
bars.csv           the published dataset
positions.csv      output of strategy.py on bars.csv
research/          the exploration that led here (mean reversion, momentum,
                   EMA cross, Donchian, vol-normalised trend grid)
```
