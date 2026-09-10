from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


class UnitsResponse(BaseModel):
    weight: Literal["kg"] = "kg"
    water: Literal["ml"] = "ml"


class SessionResponse(BaseModel):
    authenticated: Literal[True] = True
    currency: Literal["THB"] = "THB"
    timezone: Literal["Asia/Bangkok"] = "Asia/Bangkok"
    units: UnitsResponse = UnitsResponse()
