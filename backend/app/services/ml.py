from __future__ import annotations
import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA


def business_days(months: int) -> int:
    # ~21 trading days per month
    return max(1, int(months * 21))


def forecast_price_ARIMA(
    adj_close: pd.Series, horizon_months: int
) -> tuple[float, float]:
    """
    Fit a tiny ARIMA(1,1,1) and forecast price T months ahead.
    Returns (price_T, naive_confidence).
    Notes:
      - Simple, for study purposes only.
      - Fills missing days to business frequency.
    """
    y = adj_close.copy().sort_index()
    y = y.asfreq("B").ffill()
    # Guardrails for very short series
    if len(y) < 60:
        # Not enough history; assume flat
        return float(y.iloc[-1]), 0.4

    model = ARIMA(y, order=(1, 1, 1))
    fit = model.fit(method_kwargs={"warn_convergence": False})
    steps = business_days(horizon_months)
    fc = fit.forecast(steps=steps)
    pT = float(fc.iloc[-1])
    # A crude confidence proxy from residual std (smaller -> higher conf)
    resid_std = float(np.nanstd(fit.resid)) if hasattr(fit, "resid") else 0.0
    conf = max(0.3, min(0.9, 1.0 / (1.0 + resid_std / (y.iloc[-1] + 1e-6))))
    return pT, conf


def rolling_volatility(adj_close: pd.Series, window: int = 60) -> float:
    r = adj_close.pct_change().rolling(window).std().iloc[-1]
    return float(r) if pd.notna(r) else 0.0


def estimate_monthly_dy(
    dividends: pd.Series, price_now: float, months_window: int = 12
) -> float:
    """
    Approximate expected monthly dividend yield as:
      (sum of last 12 months dividends / 12) / current price
    """
    if dividends is None or len(dividends) == 0 or price_now <= 0:
        return 0.0
    cutoff = dividends.index.max() - pd.DateOffset(months=months_window)
    last12_sum = float(dividends[dividends.index >= cutoff].sum())
    return (last12_sum / max(1, months_window)) / price_now
