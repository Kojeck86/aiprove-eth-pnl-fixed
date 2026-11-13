# eth-pnl-fixed — AIProve entry

Strategy with the highest backtest PnL on the frozen ETH 1-min dataset
(1,440 bars, Binance ETH/USDT, 24h ending 2026-11-13 12:17 UTC).

## Strategy
**Donchian breakout with an ATR filter (N=120, ATR x0.5).**
- Long when the close breaks above the 120-bar high by more than 0.5 x ATR(14).
- Short when the close breaks below the 120-bar low by more than 0.5 x ATR(14).
- The position flips on the opposite breakout (so it catches the drop and the recovery).
- Signals on the close of bar i, filled at the open of bar i+1 (no lookahead).
- Fixed size: 1 ETH.

## Result (local backtest, 12 bps/side costs)
- **Net PnL: +$63.94** (buy-and-hold = -$68.09)
- Trades: 3, win rate 66.7%, max drawdown $48.56
- Robust: N=90-150 x ATR 0.5 all give +$60-64 (broad plateau, not a peak);
  profitable even at 3x the assumed cost (+$35.43 @ 36 bps/side).

## Run it
```
python3 strategy.py            # uses bars.csv in this directory
python3 strategy.py bars.csv   # explicit file
```
No dependencies beyond the Python standard library.

## Files
- `strategy.py` — the entry (self-contained: data load, ATR, signals, backtest).
- `backtest.py`, `backtest2.py`, `backtest3.py` — the exploration harness (EMA, Donchian, momentum, Bollinger, volume, trailing-stop, fine sweeps).
- `bars.csv` — the frozen dataset (from the AIProve challenge repo).
- `TRANSCRIPT.md` — full build + test log.
