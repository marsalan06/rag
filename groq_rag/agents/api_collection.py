from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import requests

# Define Pydantic models for Weather API


class WeatherResponse(BaseModel):
    coord: Optional[Dict]
    weather: Optional[List[Dict]]
    main: Optional[Dict]
    visibility: Optional[int]
    wind: Optional[Dict]
    clouds: Optional[Dict]
    dt: Optional[int]
    sys: Optional[Dict]
    timezone: Optional[int]
    id: Optional[int]
    name: Optional[str]
    cod: Optional[int]

# Define the WeatherTool


@tool
def fetch_weather(city: str) -> WeatherResponse:
    """Fetches current weather data for a specified city using RapidAPI."""
    url = f"https://open-weather13.p.rapidapi.com/city/{city}/EN"
    headers = {
        "x-rapidapi-host": "open-weather13.p.rapidapi.com",
        "x-rapidapi-key": ""
    }
    response = requests.get(url, headers=headers)
    return WeatherResponse(**response.json())

# Define Pydantic models for Yahoo Finance Logo API


class FinanceLogoParams(BaseModel):
    stock: str = Field(..., description="Stock symbol")


class FinanceLogoResponse(BaseModel):
    logo: Optional[str]

# Define the FinanceLogoTool


@tool
def fetch_finance_logo(stock: str) -> FinanceLogoResponse:
    """Fetches the logo URL for a specified stock using Yahoo Finance API."""
    url = "https://yahoo-finance160.p.rapidapi.com/getlogo"
    headers = {
        "Content-Type": "application/json",
        "x-rapidapi-host": "yahoo-finance160.p.rapidapi.com",
        "x-rapidapi-key": ""
    }
    data = {"stock": stock}
    response = requests.post(url, headers=headers, json=data)
    return FinanceLogoResponse(**response.json())
