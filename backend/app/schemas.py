from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional, Any, Dict

AssetType = Literal["stock", "fii", "generic"]


class CalcIn(BaseModel):
    target_gain_brl: float = Field(
        gt=0, description="Target gain in BRL, must be greater than 0"
    )
    asset_type: AssetType
    horizon_months: int = Field(
        gt=0,
        lt=60,
        description="Investment horizon in months, must be between 1 and 59",
    )
    ticker: Optional[str] = Field(
        default=None, description="Optional: ticker symbol of the asset"
    )

    @field_validator("ticker")
    @classmethod
    def strip_ticker(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v2 = v.strip()
        return v2 or None


class CalcOut(BaseModel):
    ticker: str
    price_now: float
    plan: Literal["Lump Sum", "DCA", "Dividends"]
    units_to_buy: int
    details: Dict[str, Any]
