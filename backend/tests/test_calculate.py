from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _post(payload):
    return client.post("/calculate", json=payload)


def test_calculate_fii_ok():
    r = _post(
        {"target_gain_brl": 1000, "asset_type": "fii", "horizon_months": 12}
    )
    assert r.status_code == 200
    data = r.json()
    assert data["plan"] == "Dividends"
    assert data["units_to_buy"] > 0
    assert "income_per_unit_T" in data["details"]


def test_calculate_acao_ok_dca_short_horizon():
    r = _post(
        {"target_gain_brl": 500, "asset_type": "stock", "horizon_months": 3}
    )
    assert r.status_code == 200
    data = r.json()
    assert data["plan"] == "DCA"
    assert data["units_to_buy"] > 0
    assert "price_forecast_T" in data["details"]


def test_calculate_generico_ok_lump_sum_long_horizon():
    r = _post(
        {"target_gain_brl": 500, "asset_type": "generic", "horizon_months": 18}
    )
    assert r.status_code == 200
    data = r.json()
    assert data["plan"] == "Lump Sum"
    assert data["units_to_buy"] > 0


def test_calculate_validation_errors():
    # target <= 0
    r = _post(
        {"target_gain_brl": 0, "asset_type": "fii", "horizon_months": 12}
    )
    assert r.status_code == 422
    # horizonte inválido
    r = _post(
        {"target_gain_brl": 100, "asset_type": "fii", "horizon_months": 0}
    )
    assert r.status_code == 422
    # asset_type inválido
    r = _post(
        {"target_gain_brl": 100, "asset_type": "cripto", "horizon_months": 6}
    )
    assert r.status_code == 422
