"""Replay strategy.py positions over bars.csv with an explicit cost model.

    python3 strategy.py bars.csv > positions.csv
    python3 backtest.py positions.csv

Costs: taker fee + half-spread/slippage per unit of position traded, charged on
every position change. Defaults are deliberately pessimistic for a small
account: 5 bp taker and 2 bp slippage per side. Nothing is filled inside the bar
- a new target is only ever applied to the *next* bar's return, so there are no
phantom fills at the price that generated the signal.
"""

import sys

TAKER = 0.0005
SLIP = 0.0002


def load_bars(path="bars.csv"):
    with open(path) as f:
        head = f.readline().strip().split(",")
        rows = [line.strip().split(",") for line in f if line.strip()]
    ci = head.index("close")
    return [float(r[ci]) for r in rows]


def replay(closes, pos, taker=TAKER, slip=SLIP, start=0, end=None):
    end = len(closes) if end is None else end
    cash = 0.0
    prev = 0.0
    trades = 0.0
    peak = 0.0
    mdd = 0.0
    gross = 0.0
    cost = 0.0
    rets = []
    for i in range(max(start, 1), end):
        r = closes[i] / closes[i - 1] - 1
        leg = pos[i - 1] * r
        gross += leg
        cash += leg
        if pos[i] != pos[i - 1]:
            c = (taker + slip) * abs(pos[i] - pos[i - 1])
            cash -= c
            cost += c
            trades += 1
        rets.append(cash - prev)
        prev = cash
        peak = max(peak, cash)
        mdd = max(mdd, peak - cash)
    sd = (sum((x - sum(rets) / len(rets)) ** 2 for x in rets) / len(rets)) ** 0.5 if rets else 0
    # Minute-bar mean/std scaled to one day; this is NOT annualized.
    sharpe = (sum(rets) / len(rets) / sd * (1440 ** 0.5)) if sd else 0.0
    return {
        "net_pct": cash * 100,
        "gross_pct": gross * 100,
        "cost_pct": cost * 100,
        "trades": trades,
        "max_dd_pct": mdd * 100,
        "sharpe": sharpe,
    }


def main():
    pfile = sys.argv[1] if len(sys.argv) > 1 else "positions.csv"
    closes = load_bars()
    with open(pfile) as f:
        head = f.readline()
        pos = [float(line.split(",")[1]) for line in f if line.strip()]
    assert len(pos) == len(closes), (len(pos), len(closes))

    full = replay(closes, pos)
    print("full window : " + "  ".join(f"{k}={v:.2f}" for k, v in full.items()))

    h = len(closes) // 2
    first = replay(closes, pos, start=0, end=h)
    tail = replay(closes, pos, start=h, end=len(closes))
    print("first half  : " + "  ".join(f"{k}={v:.2f}" for k, v in first.items()))
    print("second half : " + "  ".join(f"{k}={v:.2f}" for k, v in tail.items()))

    # cost sensitivity: what happens at 0 costs, and at triple costs
    for label, tk, sl in (("zero-cost", 0.0, 0.0), ("base", TAKER, SLIP), ("3x cost", 0.0015, 0.0006)):
        r = replay(closes, pos, taker=tk, slip=sl)
        print(f"{label:10s}: net={r['net_pct']:.2f}%  dd={r['max_dd_pct']:.2f}%  trades={r['trades']:.0f}")


if __name__ == "__main__":
    main()
