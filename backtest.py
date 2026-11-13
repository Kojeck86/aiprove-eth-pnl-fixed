#!/usr/bin/env python3
"""Backtest harness for AIProve eth-pnl-fixed (frozen ETH 1-min bars).

Cost model (documented assumptions — the spec gives no exact numbers):
- Taker fee 0.10% (10 bps) per fill, slippage 0.02% (2 bps) per fill.
- One side therefore costs 12 bps; a round trip costs 24 bps.
- Position size: 1 ETH, fixed. PnL reported in USD.
- Signals are computed on the close of bar i and executed at the OPEN of
  bar i+1 (no lookahead, no phantom fills).

Strategies output a target position in {-1, 0, +1} per bar.
"""
import csv, math, statistics

FEE_BPS = 10.0      # taker fee per fill
SLIP_BPS = 2.0      # slippage per fill
COST_BPS = FEE_BPS + SLIP_BPS   # 12 bps per side

def load(path="bars.csv"):
    rows = list(csv.DictReader(open(path)))
    o = [float(r["open"]) for r in rows]
    h = [float(r["high"]) for r in rows]
    l = [float(r["low"]) for r in rows]
    c = [float(r["close"]) for r in rows]
    v = [float(r["volume"]) for r in rows]
    return o, h, l, c, v

def ema(series, period):
    k = 2.0 / (period + 1)
    out = [series[0]]
    for x in series[1:]:
        out.append(x * k + out[-1] * (1 - k))
    return out

def backtest(opens, closes, target):
    """target[i] = desired position {-1,0,1} decided at close of bar i.
    Executed at open of bar i+1. Returns (net_pnl, trades, win_rate, max_dd, equity_curve)."""
    n = len(closes)
    pos = 0            # current position
    cash = 0.0         # realised PnL
    trades = 0
    wins = 0
    equity = [0.0]     # equity curve (mark-to-market)
    peak = 0.0
    max_dd = 0.0
    for i in range(n - 1):
        desired = target[i]
        if desired != pos:
            # close old position at next open
            px = opens[i + 1]
            if pos != 0:
                cash += pos * (px - entry_px)
                cash -= abs(px) * COST_BPS / 10000.0
                trades += 1
                if pos * (px - entry_px) > 0:
                    wins += 1
            # open new position at next open
            if desired != 0:
                entry_px = px
                cash -= abs(px) * COST_BPS / 10000.0
            pos = desired
        # mark-to-market equity
        mtm = cash + (pos * (closes[i + 1] - entry_px) if pos != 0 else 0.0)
        equity.append(mtm)
        if mtm > peak:
            peak = mtm
        dd = peak - mtm
        if dd > max_dd:
            max_dd = dd
    # close any open position at final close
    if pos != 0:
        cash += pos * (closes[-1] - entry_px)
        cash -= abs(closes[-1]) * COST_BPS / 10000.0
        trades += 1
        if pos * (closes[-1] - entry_px) > 0:
            wins += 1
    win_rate = wins / trades if trades else 0.0
    return cash, trades, win_rate, max_dd, equity

# ---------- strategies ----------
def strat_ema_cross(closes, fast, slow):
    ef, es = ema(closes, fast), ema(closes, slow)
    return [1 if ef[i] > es[i] else -1 for i in range(len(closes))]

def strat_donchian(highs, lows, closes, n):
    out = []
    for i in range(len(closes)):
        if i < n:
            out.append(0)
            continue
        hi = max(highs[i - n:i])
        lo = min(lows[i - n:i])
        if closes[i] > hi:
            out.append(1)
        elif closes[i] < lo:
            out.append(-1)
        else:
            out.append(out[-1] if out else 0)
    return out

def strat_momentum(closes, n):
    out = []
    for i in range(len(closes)):
        if i < n:
            out.append(0)
        else:
            out.append(1 if closes[i] > closes[i - n] else -1)
    return out

def strat_bollinger(closes, n, k):
    out = []
    for i in range(len(closes)):
        if i < n:
            out.append(0)
            continue
        w = closes[i - n + 1:i + 1]
        m = statistics.mean(w)
        s = statistics.pstdev(w)
        if closes[i] < m - k * s:
            out.append(1)      # oversold -> long
        elif closes[i] > m + k * s:
            out.append(-1)     # overbought -> short
        else:
            out.append(out[-1] if out else 0)
    return out

def report(name, pnl, trades, wr, dd):
    print(f"{name:38s} PnL ${pnl:8.2f}  trades {trades:3d}  win {wr:5.1%}  maxDD ${dd:7.2f}")

if __name__ == "__main__":
    o, h, l, c, v = load()
    n = len(c)
    # baseline: buy & hold 1 ETH
    print(f"buy-hold 1 ETH: ${c[-1]-c[0]:.2f}")
    print()
    print("== EMA crossover (long/short, always in) ==")
    best = None
    for fast in (5, 9, 12, 21):
        for slow in (26, 50, 100, 200):
            if fast >= slow:
                continue
            t = strat_ema_cross(c, fast, slow)
            pnl, tr, wr, dd, _ = backtest(o, c, t)
            report(f"EMA {fast}/{slow}", pnl, tr, wr, dd)
            if best is None or pnl > best[0]:
                best = (pnl, fast, slow, tr, wr, dd)
    print("best EMA:", best)
    print()
    print("== Donchian breakout ==")
    best_d = None
    for nn in (10, 20, 30, 60, 120):
        t = strat_donchian(h, l, c, nn)
        pnl, tr, wr, dd, _ = backtest(o, c, t)
        report(f"Donchian {nn}", pnl, tr, wr, dd)
        if best_d is None or pnl > best_d[0]:
            best_d = (pnl, nn, tr, wr, dd)
    print("best Donchian:", best_d)
    print()
    print("== Momentum (N-bar return sign) ==")
    best_m = None
    for nn in (10, 30, 60, 120, 240):
        t = strat_momentum(c, nn)
        pnl, tr, wr, dd, _ = backtest(o, c, t)
        report(f"Momentum {nn}", pnl, tr, wr, dd)
        if best_m is None or pnl > best_m[0]:
            best_m = (pnl, nn, tr, wr, dd)
    print("best Momentum:", best_m)
    print()
    print("== Bollinger mean reversion ==")
    best_b = None
    for nn in (20, 40):
        for k in (1.5, 2.0, 2.5):
            t = strat_bollinger(c, nn, k)
            pnl, tr, wr, dd, _ = backtest(o, c, t)
            report(f"Bollinger {nn} k={k}", pnl, tr, wr, dd)
            if best_b is None or pnl > best_b[0]:
                best_b = (pnl, nn, k, tr, wr, dd)
    print("best Bollinger:", best_b)
