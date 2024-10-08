import requests
from langchain_core.tools import tool
from pydantic import BaseModel
from typing import Optional, Dict, Any


class Condition(BaseModel):
    text: str
    icon: str
    code: int


class CurrentWeather(BaseModel):
    last_updated_epoch: int
    last_updated: str
    temp_c: float
    temp_f: float
    is_day: int
    condition: Condition
    wind_mph: float
    wind_kph: float
    wind_degree: int
    wind_dir: str
    pressure_mb: float
    pressure_in: float
    precip_mm: float
    precip_in: float
    humidity: int
    cloud: int
    feelslike_c: float
    feelslike_f: float
    windchill_c: float
    windchill_f: float
    heatindex_c: float
    heatindex_f: float
    dewpoint_c: float
    dewpoint_f: float
    vis_km: float
    vis_miles: float
    uv: float
    gust_mph: float
    gust_kph: float


class Location(BaseModel):
    name: str
    region: str
    country: str
    lat: float
    lon: float
    tz_id: str
    localtime_epoch: int
    localtime: str


class WeatherAPIResponse(BaseModel):
    location: Location
    current: CurrentWeather


@tool
def fetch_current_weather(city: str) -> WeatherAPIResponse:
    """Fetches current weather data for a specified city using the WeatherAPI."""
    url = f"https://weatherapi-com.p.rapidapi.com/current.json?q={city}"
    headers = {
        "x-rapidapi-host": "weatherapi-com.p.rapidapi.com",
        "x-rapidapi-key": "7250a600cdmsh119523d2404f91dp12acf6jsn62fb1c2d98ec"
    }

    response = requests.get(url, headers=headers)
    response_data = response.json()

    return WeatherAPIResponse(**response_data)
