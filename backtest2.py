#!/usr/bin/env python3
"""Round 2: strategies that survive the chop and catch the breakdown.

Hypothesis from data: bars 0-840 chop sideways ~$1990-2029; bars ~840-1062
drop to $1907; bars 1062-1440 recover to $1960. The edge is (a) staying flat
in the chop, (b) shorting the breakdown, (c) covering near the bottom.
"""
from backtest import load, backtest, ema, report
import statistics

o, h, l, c, v = load()
n = len(c)

def atr(highs, lows, closes, period=14):
    tr = [highs[0] - lows[0]]
    for i in range(1, len(closes)):
        tr.append(max(highs[i] - lows[i],
                      abs(highs[i] - closes[i - 1]),
                      abs(lows[i] - closes[i - 1])))
    return ema(tr, period)

def strat_donchian_atr(highs, lows, closes, n_, atr_mult):
    """Breakout of N-bar range, but only if the close is beyond the range by
    atr_mult * ATR (filters chop breakouts)."""
    a = atr(highs, lows, closes, 14)
    out = []
    for i in range(len(closes)):
        if i < n_:
            out.append(0)
            continue
        hi = max(highs[i - n_:i])
        lo = min(lows[i - n_:i])
        if closes[i] > hi + atr_mult * a[i]:
            out.append(1)
        elif closes[i] < lo - atr_mult * a[i]:
            out.append(-1)
        else:
            out.append(out[-1] if out else 0)
    return out

def strat_ema_filtered(closes, fast, slow, trend):
    """EMA cross, but only take the signal when the slow EMA direction agrees
    with a longer trend EMA (reduces chop whipsaws)."""
    ef, es, et = ema(closes, fast), ema(closes, slow), ema(closes, trend)
    out = []
    for i in range(len(closes)):
        if ef[i] > es[i] and es[i] > et[i]:
            out.append(1)
        elif ef[i] < es[i] and es[i] < et[i]:
            out.append(-1)
        else:
            out.append(0)
    return out

def strat_vol_breakout(closes, volumes, n_, vol_mult):
    """Breakout of N-bar range confirmed by volume above vol_mult x the
    N-bar mean volume."""
    out = []
    for i in range(len(closes)):
        if i < n_:
            out.append(0)
            continue
        hi = max(closes[i - n_:i])
        lo = min(closes[i - n_:i])
        mv = statistics.mean(volumes[i - n_:i])
        if closes[i] > hi and volumes[i] > vol_mult * mv:
            out.append(1)
        elif closes[i] < lo and volumes[i] > vol_mult * mv:
            out.append(-1)
        else:
            out.append(out[-1] if out else 0)
    return out

def strat_donchian_trail(highs, lows, closes, n_, exit_n):
    """Donchian entry, exit on opposite N2-bar extreme (faster exit)."""
    out = []
    pos = 0
    for i in range(len(closes)):
        if i < n_:
            out.append(0)
            continue
        hi = max(highs[i - n_:i])
        lo = min(lows[i - n_:i])
        if pos == 0:
            if closes[i] > hi:
                pos = 1
            elif closes[i] < lo:
                pos = -1
        elif pos == 1:
            if closes[i] < min(lows[i - exit_n:i]):
                pos = 0
        elif pos == -1:
            if closes[i] > max(highs[i - exit_n:i]):
                pos = 0
        out.append(pos)
    return out

print("== Donchian + ATR filter ==")
best = None
for nn in (60, 120, 180, 240):
    for am in (0.0, 0.5, 1.0, 1.5):
        t = strat_donchian_atr(h, l, c, nn, am)
        pnl, tr, wr, dd, _ = backtest(o, c, t)
        report(f"DonchianATR {nn} x{am}", pnl, tr, wr, dd)
        if best is None or pnl > best[0]:
            best = (pnl, nn, am, tr, wr, dd)
print("best:", best)
print()
print("== EMA cross + trend filter ==")
best2 = None
for fast, slow, trend in [(9, 26, 100), (12, 50, 200), (21, 50, 200),
                          (9, 50, 200), (21, 100, 300), (12, 26, 100)]:
    t = strat_ema_filtered(c, fast, slow, trend)
    pnl, tr, wr, dd, _ = backtest(o, c, t)
    report(f"EMAfilt {fast}/{slow}/{trend}", pnl, tr, wr, dd)
    if best2 is None or pnl > best2[0]:
        best2 = (pnl, fast, slow, trend, tr, wr, dd)
print("best:", best2)
print()
print("== Volume-confirmed breakout ==")
best3 = None
for nn in (60, 120, 180):
    for vm in (1.0, 1.5, 2.0):
        t = strat_vol_breakout(c, v, nn, vm)
        pnl, tr, wr, dd, _ = backtest(o, c, t)
        report(f"VolBrk {nn} x{vm}", pnl, tr, wr, dd)
        if best3 is None or pnl > best3[0]:
            best3 = (pnl, nn, vm, tr, wr, dd)
print("best:", best3)
print()
print("== Donchian + fast exit ==")
best4 = None
for nn in (60, 120, 180):
    for en in (5, 10, 20):
        t = strat_donchian_trail(h, l, c, nn, en)
        pnl, tr, wr, dd, _ = backtest(o, c, t)
        report(f"DonchianTrail {nn}/{en}", pnl, tr, wr, dd)
        if best4 is None or pnl > best4[0]:
            best4 = (pnl, nn, en, tr, wr, dd)
print("best:", best4)
