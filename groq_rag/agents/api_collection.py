from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import requests
from langchain.memory.simple import SimpleMemory
import redis

redis_client = redis.StrictRedis(
    host='172.17.0.2', port=6379, db=0, decode_responses=True)
redis_client.set("session_expired", int(False))  # Store as 0


# Initialize memory to store session_id
memory = SimpleMemory(memories={
    # Initially, set to True to ensure login is called first
    "db": "",
    "username": ".@.com",
    "password": ""
})
# Define Pydantic models for Weather API


class ErrorData(BaseModel):
    code: int
    message: str
    name: Optional[str] = None
    debug: Optional[str] = None


class ErrorResponse(BaseModel):
    jsonrpc: str
    id: Optional[int]
    error: ErrorData


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
def check_session_status() -> bool:
    """Checks if the session ID is present and not expired in Redis."""
    session_id = redis_client.get("session_id")
    # Redis stores everything as strings
    session_expired = bool(int(redis_client.get("session_expired"))) == "True"

    if session_id and not session_expired:
        return True
    else:
        return False


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


# Pydantic Models for Sales Order
class SaleOrder(BaseModel):
    id: int
    name: str
    state: str
    date_order: str
    amount_total: float
    # Add other relevant fields here


class SaleOrderData(BaseModel):
    current: int
    total_pages: int
    length_record: int
    record: List[SaleOrder]


class SaleOrderResponse(BaseModel):
    status_code: int
    message: str
    data: SaleOrderData


class SaleOrderAPIResponse(BaseModel):
    jsonrpc: str
    id: Optional[int]
    result: Optional[SaleOrderResponse]
    success: Optional[bool] = None

# Tool to login and get session_id


@tool
def login_to_odoo() -> str:
    """Logs in to the Odoo API and retrieves the session_id, updating the session status in memory."""

    url = "http://0.0.0.0:8069/api/auth/login"

    db = memory.memories.get("db")
    username = memory.memories.get("username")
    password = memory.memories.get("password")

    headers = {
        "Content-Type": "application/json",
    }
    payload = {
        "db": db,
        "username": username,
        "password": password,
    }
    response = requests.post(url, headers=headers, json=payload)

    # Extract session_id from the response cookies
    session_id = response.cookies.get("session_id")

    if not session_id:
        raise ValueError("Failed to retrieve session_id from the response.")
    redis_client.set("session_id", session_id)
    redis_client.set("session_expired", int(False))  # Mark session as valid
    # Set TTL for 24 hours or adjust as needed
    redis_client.expire("session_id", 60*60*24)

    return session_id

# Tool to fetch sales orders using the session_id


@tool
def fetch_sale_orders(session_id: str) -> SaleOrderAPIResponse:
    """Fetches sale orders using the provided API endpoint."""

    session_id = redis_client.get("session_id")
    if not session_id:
        return ErrorResponse(jsonrpc="2.0", id=None, error=ErrorData(code=100, message="No session_id available. Please log in first."))

    url = "http://0.0.0.0:8069/api/model/sale.order"
    headers = {
        "Content-Type": "application/json",
        "Cookie": f"session_id={session_id}"
    }
    data = {}

    response = requests.get(url, headers=headers, json=data)
    response_data = response.json()

    # If there's an error in the response, return it
    if 'error' in response_data:
        redis_client.set("session_expired", int(True)
                         )  # Mark session as expired
        return ErrorResponse(**response_data)

    redis_client.set("session_expired", int(False))
    # If successful, return the sale order data
    return SaleOrderAPIResponse(**response_data)
