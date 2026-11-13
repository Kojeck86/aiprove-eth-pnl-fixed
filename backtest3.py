#!/usr/bin/env python3
"""Round 3: fine sweep around the robust region + trailing-stop exit."""
from backtest import load, backtest, ema, report
from backtest2 import strat_donchian_atr, atr

o, h, l, c, v = load()

def strat_donchian_trailstop(highs, lows, closes, n_, atr_mult, trail_mult):
    """Donchian+ATR entry; exit via ATR trailing stop from the extreme
    reached while in the trade (lets winners run, cuts losers)."""
    a = atr(highs, lows, closes, 14)
    out = []
    pos = 0
    extreme = None
    for i in range(len(closes)):
        if i < n_:
            out.append(0)
            continue
        hi = max(highs[i - n_:i])
        lo = min(lows[i - n_:i])
        if pos == 0:
            if closes[i] > hi + atr_mult * a[i]:
                pos = 1
                extreme = closes[i]
            elif closes[i] < lo - atr_mult * a[i]:
                pos = -1
                extreme = closes[i]
        elif pos == 1:
            extreme = max(extreme, closes[i])
            if closes[i] < extreme - trail_mult * a[i]:
                pos = 0
        elif pos == -1:
            extreme = min(extreme, closes[i])
            if closes[i] > extreme + trail_mult * a[i]:
                pos = 0
        out.append(pos)
    return out

print("== Fine sweep: DonchianATR N x mult ==")
results = []
for nn in (90, 100, 110, 120, 130, 140, 150):
    row = []
    for am in (0.25, 0.4, 0.5, 0.6, 0.75):
        t = strat_donchian_atr(h, l, c, nn, am)
        pnl, tr, wr, dd, _ = backtest(o, c, t)
        row.append(f"{pnl:7.2f}")
        results.append((pnl, nn, am, tr, wr, dd))
    print(f"N={nn:3d}: " + "  ".join(row) + "   (mult 0.25/0.4/0.5/0.6/0.75)")
results.sort(reverse=True)
print("top 5:", [(round(r[0], 2), r[1], r[2], r[3]) for r in results[:5]])
print()
print("== Trailing-stop exit (entry DonchianATR) ==")
best = None
for nn in (120, 180):
    for am in (0.5, 1.0):
        for tm in (1.0, 1.5, 2.0, 3.0):
            t = strat_donchian_trailstop(h, l, c, nn, am, tm)
            pnl, tr, wr, dd, _ = backtest(o, c, t)
            report(f"TrailStop {nn} x{am} trail{tm}", pnl, tr, wr, dd)
            if best is None or pnl > best[0]:
                best = (pnl, nn, am, tm, tr, wr, dd)
print("best trailstop:", best)
