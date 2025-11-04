from fastapi.testclient import TestClient
from app.main import app
import pandas as pd
import numpy as np
from datetime import datetime

client = TestClient(app)


def _fake_hist():
    # 250 business days, drifting series
    dates = pd.bdate_range(end=datetime.today(), periods=250)
    price = 100 + np.cumsum(np.random.normal(0, 0.5, size=len(dates)))
    df = pd.DataFrame({"Adj Close": price}, index=dates)
    return df


def _fake_divs():
    # 12 monthly dividends of 0.8
    today = datetime.today()
    idx = [today - pd.DateOffset(months=i) for i in range(1, 13)]
    s = pd.Series([0.8] * 12, index=sorted(idx))
    return s


def test_calculate_real_fii_with_mocks(monkeypatch):
    from app.services import data

    monkeypatch.setattr(data, "get_price_history", lambda t: _fake_hist())
    monkeypatch.setattr(data, "get_dividends", lambda t: _fake_divs())
    monkeypatch.setattr(data, "get_cdi_annual_rate", lambda default=0.1: 0.12)

    r = client.post(
        "/calculate",
        json={
            "target_gain_brl": 1000,
            "asset_type": "fii",
            "horizon_months": 12,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["plan"] in ["Dividendos", "DCA"]  # rule may pick Dividendos
    assert body["units_to_buy"] > 0
    assert "income_per_unit_T" in body["details"]


def test_calculate_real_stock_with_mocks(monkeypatch):
    from app.services import data

    monkeypatch.setattr(data, "get_price_history", lambda t: _fake_hist())
    monkeypatch.setattr(data, "get_dividends", lambda t: _fake_divs())
    monkeypatch.setattr(data, "get_cdi_annual_rate", lambda default=0.1: 0.12)

    r = client.post(
        "/calculate",
        json={
            "target_gain_brl": 500,
            "asset_type": "acao",
            "horizon_months": 6,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["units_to_buy"] > 0
    assert "price_forecast_T" in body["details"]
