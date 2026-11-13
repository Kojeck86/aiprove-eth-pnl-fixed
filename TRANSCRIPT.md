# Transcript — eth-pnl-fixed build + backtest

## Dataset
- `bars.csv` — 1,440 ETH/USDT 1-min bars (Binance, 24h ending 2026-11-13 12:17 UTC), from the AIProve eth-backtest challenge.
- First close $2,028.68, last close $1,960.59 (-3.36%). Buy-and-hold 1 ETH = -$68.09.
- Structure: bars 0-840 chop sideways ($1,990-2,029); bars ~840-1062 sharp drop to $1,906.99; bars 1062-1440 recover to $1,960.59.

## Cost model (assumptions — the spec gives no exact numbers)
- Taker fee 0.10% (10 bps) + slippage 0.02% (2 bps) = 12 bps per fill.
- Position size 1 ETH, fixed. Signals on the close of bar i, filled at the open of bar i+1 (no lookahead, no phantom fills).

## Strategies tested (all in backtest.py / backtest2.py / backtest3.py)
- EMA crossover (fast/slow): best -$68.48 (21/200). All negative — whipsaws + fees.
- Donchian breakout: best -$6.59 (N=120). Near breakeven.
- Momentum (N-bar return sign): best -$187.90. All negative.
- Bollinger mean reversion: best -$76.64. All negative.
- EMA cross + trend filter: best -$39.23. All negative.
- Volume-confirmed breakout: best +$44.01 (N=180).
- Donchian + ATR filter: **best +$63.94 (N=120, ATR x0.5), 3 trades, 66.7% win, maxDD $48.56.**
- Donchian + trailing-stop exit: all negative (worst -$28.61). Opposite-breakout exit is better.

## Parameter robustness (Donchian + ATR filter)
Fine sweep, net PnL:
- N=90-120 x ATR 0.4-0.75: +$63.94 (identical 3 trades).
- N=130-150 x ATR 0.5: +$60.23.
- N=60 x ATR 1.0: +$53.10; N=180 x ATR 0-0.5: +$44.01; N=240 x ATR 0: +$60.66.
- The chosen point (N=120, ATR x0.5) sits in the centre of a broad +$60-64 plateau across N=90-150, not a sharp peak. The slightly higher N=130/140 x ATR 0.25 (+$67.50) was rejected: ATR 0.25 is not robust across N (it gives -$6.59 at N=90-120).

## Cost sensitivity (chosen strategy, N=120 x ATR 0.5)
- 0 bps/side: +$78.19
- 6 bps/side: +$71.06
- 12 bps/side: +$63.94
- 24 bps/side: +$49.68
- 36 bps/side: +$35.43
Profitable even at 3x the assumed cost.

## Final run (python3 strategy.py)
```
bars: 1440  first close 2028.68  last close 1960.59
strategy: Donchian N=120 + ATR x0.5 (ATR14)
net PnL (1 ETH, 12 bps/side): $63.94
trades: 3  win rate: 66.7%  max drawdown: $48.56
trade log (bar, action, side, entry, exit, pnl):
  (228, 'open', 1, 2021.10, None, None)
  (619, 'close', 1, 2021.10, 2008.93, -12.17)
  (619, 'open', -1, 2008.93, None, None)
  (1094, 'close', -1, 2008.93, 1939.58, +69.35)
  (1094, 'open', 1, 1939.58, None, None)
  (1439, 'close', 1, 1939.58, 1960.59, +21.01)
```
