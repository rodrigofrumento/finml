from fastapi import FastAPI
from .schemas import CalcIn, CalcOut
from .services.calculator import calculate_real

app = FastAPI(title="Fin-ML Planner (MVP)")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/calculate", response_model=CalcOut)
def calculate(inp: CalcIn):
    """
    Uses real market data (yfinance) and a tiny ARIMA for study-only forecasts.
    """
    return calculate_real(inp)
