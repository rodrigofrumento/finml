import datetime as dt
import pandas as pd
import requests
import yfinance as yf
import os

YF_PERIOD = os.getenv("YF_PERIOD", "5y")
YF_INTERVAL = os.getenv("YF_INTERVAL", "1d")


def _select_adj_close(df: pd.DataFrame, ticker: str) -> pd.Series:
    """
    Return a single-column Series with adjusted close.
    Handles cases where df has MultiIndex columns and/or Adj Close
    Falls back to Close if Adj Close not found.
    """
    cols = df.columns

    if isinstance(cols, pd.MultiIndex):
        candidates = []
        if ("Adj Close", ticker) in cols:
            candidates.append(("Adj Close", ticker))
        if ("Adj Close", "") in cols:
            candidates.append(("Adj Close", ""))

        candidates += [c for c in cols if isinstance(c, tuple) and c[0] == "Adj Close"]
        for c in candidates:
            s = df[c].dropna()
            if not s.empty:
                s.name = "Adj Close"
                return s
            
        close_candidates = []
        if ("Close", ticker) in cols:
            close_candidates.append(("Close", ticker))
        close_candidates += [c for c in cols if isinstance(c, tuple) and c[0] == "Close"]
        for c in close_candidates:
            s = df[c].dropna()
            if not s.empty:
                s.name = "Adj Close"
                return s

        raise ValueError("Could not find Adj Close or Close in MultiIndex columns")
    
    # Single-level columns: prefer 'Adj Close', fallback to 'Close'
    if "Adj Close" in df.columns:
        s = df["Adj Close"].dropna()
        if not s.empty:
            return s
    if "Close" in df.columns:
        s = df["Close"].dropna()
        if not s.empty:
            s.name = "Adj Close"
            return s

    raise ValueError("No Adj Close or Close column available")


def get_price_history(ticker: str, period: str = YF_PERIOD, interval: str = YF_INTERVAL) -> pd.DataFrame:
    """
    Returns a DataFrame with a single column 'Adj Close' indexed by DatetimeIndex (tz-naive).
    Robust to MultiIndex columns and to missing 'Adj Close'.
    """
    df = yf.download(
        ticker,
        period=period,
        interval=interval,
        progress=False,
        group_by="column",   # helps avoid MultiIndex in many cases
        auto_adjust=False    # keep both Close/Adj Close if available
    )

    if df is None or df.empty:
        raise ValueError(f"No price data for {ticker}")

    # Normalize index to tz-naive
    df.index = pd.to_datetime(df.index).tz_localize(None)

    # Extract a single Series for adjusted close
    adj = _select_adj_close(df, ticker)

    # Return as a 1-col frame named 'Adj Close' for downstream consistency
    out = adj.to_frame(name="Adj Close")
    return out


def get_dividends(ticker: str) -> pd.Series:
    """
    Returns a Series of dividends (values) indexed by DatetimeIndex.
    """
    t = yf.Ticker(ticker)
    divs = t.dividends
    if divs is None:
        return pd.Series(dtype=float)
    divs.index = pd.to_datetime(divs.index).tz_localize(None)
    return divs


def get_cdi_annual_rate(default: float = 0.10) -> float:
    """
    Fetch CDI annual rate (as decimal, e.g., 0.13 == 13% a.a.).
    Uses BCB/SGS series 12 (CDI) JSON. Falls back to `default` on error.
    """
    try:
        # last 400 days window to ensure we find a recent point
        end = dt.date.today()
        start = end - dt.timedelta(days=400)
        baseUrl = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados"
        format = "formato=json"
        url = f"{baseUrl}?{format}&dataInicial={start.strftime('%d/%m/%Y')}&dataFinal={end.strftime('%d/%m/%Y')}"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        rows = r.json()
        if not rows:
            return default
        last_val = float(rows[-1]["valor"].replace(",", "."))
        # CDI from SGS is typically in % a.a.; convert to decimal
        return last_val / 100.0
    except Exception:
        return default
