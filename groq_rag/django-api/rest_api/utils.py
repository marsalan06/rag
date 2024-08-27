from pydantic import BaseModel
from typing import Optional, List
# Pydantic models for output parsing


class Company(BaseModel):
    id: int
    name: str


class User(BaseModel):
    id: int
    name: str


class SaleOrder(BaseModel):
    id: int
    name: str
    state: Optional[str] = None
    date_order: Optional[str] = None
    amount_total: float
    company_id: Company
    user_id: User


class SaleOrderResponse(BaseModel):
    sale_orders: List[SaleOrder]
    tool_type: str


class WeatherCondition(BaseModel):
    text: str
    icon: str


class CurrentWeather(BaseModel):
    temperature_c: float
    temperature_f: float
    condition: WeatherCondition
    wind_speed_mph: float
    wind_speed_kph: float
    wind_direction: str
    pressure_mb: float
    humidity: int
    feels_like_c: float
    feels_like_f: float
    visibility_km: float
    uv_index: float


class WeatherAPIResponse(BaseModel):
    current_weather: CurrentWeather
    tool_type: str
