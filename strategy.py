#!/usr/bin/env python3
"""AIProve eth-pnl-fixed — final strategy.

Donchian breakout with an ATR filter (N=120, ATR x0.5).

Why this: the frozen 24h window is mostly chop ($1990-2029) with one large
breakdown (~$2000 -> $1907, bars ~840-1062) and a recovery to $1960.
Plain trend rules whipsaw in the chop and lose to fees; the ATR filter keeps
the strategy flat in the chop and only takes breakouts that clear the recent
range by half an ATR. The position flips on the opposite breakout, so it
catches the drop AND the recovery.

Parameter robustness (net PnL, 1 ETH, 12 bps/side costs):
  N=90..150 x ATR 0.5 all give +$60..64 — a broad plateau, not a peak.
  N=120 x ATR 0.5 = +$63.94 (centre of the plateau).
  Cost sensitivity: +$78.19 @ 0 bps, +$63.94 @ 12 bps, +$49.68 @ 24 bps,
  +$35.43 @ 36 bps — profitable even at 3x the assumed cost.

Usage:
  python3 strategy.py            # prints positions + summary for bars.csv
  python3 strategy.py bars.csv   # same, explicit file
"""
import csv
import sys


def load(path="bars.csv"):
    rows = list(csv.DictReader(open(path)))
    o = [float(r["open"]) for r in rows]
    h = [float(r["high"]) for r in rows]
    l = [float(r["low"]) for r in rows]
    c = [float(r["close"]) for r in rows]
    return o, h, l, c


def ema(series, period):
    k = 2.0 / (period + 1)
    out = [series[0]]
    for x in series[1:]:
        out.append(x * k + out[-1] * (1 - k))
    return out


def atr(highs, lows, closes, period=14):
    tr = [highs[0] - lows[0]]
    for i in range(1, len(closes)):
        tr.append(max(highs[i] - lows[i],
                      abs(highs[i] - closes[i - 1]),
                      abs(lows[i] - closes[i - 1])))
    return ema(tr, period)


# --- parameters (centre of the robust plateau) ---
N = 120          # Donchian lookback (bars)
ATR_MULT = 0.5   # breakout must clear the range by this x ATR(14)
FEE_BPS = 10.0   # taker fee per fill (assumed)
SLIP_BPS = 2.0   # slippage per fill (assumed)


def positions(highs, lows, closes, n=N, atr_mult=ATR_MULT):
    """Target position {-1, 0, +1} decided at the close of each bar.
    Executed at the open of the next bar (no lookahead)."""
    a = atr(highs, lows, closes, 14)
    out = []
    for i in range(len(closes)):
        if i < n:
            out.append(0)
            continue
        hi = max(highs[i - n:i])
        lo = min(lows[i - n:i])
        if closes[i] > hi + atr_mult * a[i]:
            out.append(1)
        elif closes[i] < lo - atr_mult * a[i]:
            out.append(-1)
        else:
            out.append(out[-1] if out else 0)
    return out


def backtest(opens, closes, target, cost_bps=FEE_BPS + SLIP_BPS):
    """Replay with fills at the next bar's open. Returns a summary dict."""
    n = len(closes)
    pos = 0
    cash = 0.0
    trades = 0
    wins = 0
    peak = 0.0
    max_dd = 0.0
    log = []
    entry_px = None
    for i in range(n - 1):
        desired = target[i]
        if desired != pos:
            px = opens[i + 1]
            if pos != 0:
                pnl = pos * (px - entry_px)
                cash += pnl
                cash -= abs(px) * cost_bps / 10000.0
                trades += 1
                if pnl > 0:
                    wins += 1
                log.append((i + 1, "close", pos, entry_px, px, pnl))
            if desired != 0:
                entry_px = px
                cash -= abs(px) * cost_bps / 10000.0
                log.append((i + 1, "open", desired, px, None, None))
            pos = desired
        mtm = cash + (pos * (closes[i + 1] - entry_px) if pos != 0 else 0.0)
        peak = max(peak, mtm)
        max_dd = max(max_dd, peak - mtm)
    if pos != 0:
        pnl = pos * (closes[-1] - entry_px)
        cash += pnl
        cash -= abs(closes[-1]) * cost_bps / 10000.0
        trades += 1
        if pnl > 0:
            wins += 1
        log.append((n - 1, "close", pos, entry_px, closes[-1], pnl))
    return {
        "net_pnl": cash,
        "trades": trades,
        "win_rate": wins / trades if trades else 0.0,
        "max_drawdown": max_dd,
        "log": log,
    }


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "bars.csv"
    o, h, l, c = load(path)
    tgt = positions(h, l, c)
    res = backtest(o, c, tgt)
    print(f"bars: {len(c)}  first close {c[0]:.2f}  last close {c[-1]:.2f}")
    print(f"strategy: Donchian N={N} + ATR x{ATR_MULT} (ATR14)")
    print(f"net PnL (1 ETH, {FEE_BPS + SLIP_BPS:.0f} bps/side): "
          f"${res['net_pnl']:.2f}")
    print(f"trades: {res['trades']}  win rate: {res['win_rate']:.1%}  "
          f"max drawdown: ${res['max_drawdown']:.2f}")
    print("trade log (bar, action, side, entry, exit, pnl):")
    for row in res["log"]:
        print(" ", row)
