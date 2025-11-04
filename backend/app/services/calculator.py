import math
from typing import Dict, Any
from ..schemas import CalcIn, CalcOut
from .data import get_price_history, get_dividends, get_cdi_annual_rate
from .ml import forecast_price_ARIMA, rolling_volatility, estimate_monthly_dy

EPS = 1e-6


def _decide_plan(asset_type: str, sigma: float) -> str:
    if asset_type == "fii":
        return "Dividendos"
    # Simple rule-of-thumb for study:
    return "DCA" if sigma > 0.07 else "Lump Sum"


def _default_ticker(asset_type: str) -> str:
    # Sensible BR defaults for learning; user can pass their own
    return {"fii": "HGLG11.SA", "acao": "ITSA4.SA"}.get(
        asset_type, "BOVA11.SA"
    )


def calculate_real(inp: CalcIn) -> CalcOut:
    ticker = inp.ticker or _default_ticker(inp.asset_type)

    # ---- Fetch data
    hist = get_price_history(ticker)
    adj = hist["Adj Close"]
    p0 = float(adj.iloc[-1])
    cdi = get_cdi_annual_rate()  # not used in formulas yet; returned as note

    if inp.asset_type == "fii":
        # Income-focused logic
        divs = get_dividends(ticker)
        ym = estimate_monthly_dy(divs, p0)  # monthly DY (decimal)
        income_per_unit_T = ym * p0 * inp.horizon_months
        income_per_unit_T = max(income_per_unit_T, 0.01)
        units = math.ceil(inp.target_gain_brl / income_per_unit_T)
        sigma = rolling_volatility(adj)
        plan = _decide_plan(inp.asset_type, sigma)
        details: Dict[str, Any] = {
            "expected_monthly_yield": round(ym, 6),
            "income_per_unit_T": round(income_per_unit_T, 2),
            "volatility_60d": round(sigma, 4),
            "cdi_annual": round(cdi, 4),
        }
    else:
        # Price-focused logic (with a tiny ARIMA)
        pT, conf = forecast_price_ARIMA(adj, inp.horizon_months)
        delta = max(pT - p0, 0.01)
        units = math.ceil(inp.target_gain_brl / delta)
        sigma = rolling_volatility(adj)
        plan = _decide_plan(inp.asset_type, sigma)
        details = {
            "price_forecast_T": round(pT, 2),
            "gain_per_unit_T": round(delta, 2),
            "volatility_60d": round(sigma, 4),
            "confidence": round(conf, 3),
            "cdi_annual": round(cdi, 4),
        }

    return CalcOut(
        ticker=ticker,
        price_now=round(p0, 2),
        plan=plan,
        units_to_buy=int(units),
        details=details,
    )
