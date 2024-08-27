from langchain_core.tools import tool
from jsonrpcclient import request, parse, Ok
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Tuple
import requests
from .connection_utils import memory, redis_client
from pydantic import ValidationError


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
def check_session_status() -> dict:
    """Checks if the session has expired by looking up the user in Redis.
    If no username is found in memory, returns a message prompting for username and password."""

    # Retrieve the username from memory
    username = memory.memories.get("username")

    if not username:
        return {
            "status": False,
            "message": "Username not found in memory. Please provide your username and password."
        }

    # Retrieve user info from Redis
    user_info = redis_client.hgetall(f"user_session_{username}")

    # Check if session exists and is not expired
    session_active = user_info.get(
        "session_expired") == "0"  # 0 means not expired
    user_id = user_info.get("user_id")

    if user_id and session_active:
        return {
            "status": True,
            "message": "Session is active."
        }
    else:
        return {
            "status": False,
            "message": "Session has expired. Please log in again."
        }


@tool
def store_user_credentials(username: str, password: str) -> dict:
    """Stores the provided username and password in memory."""

    # Store the username and password in memory
    memory.memories["username"] = username
    memory.memories["password"] = password

    return {
        "status": True,
        "message": "Username and password have been stored in memory."
    }


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
    state: Optional[str] = Field(None)
    date_order: Optional[str] = Field(None)
    amount_total: float
    company_id: Optional[Tuple[int, str]] = Field(None)
    user_id: Optional[Tuple[int, str]] = Field(None)

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


@tool
def fetch_sale_orders_by_user_id(session_id: str, user_id: int = None) -> SaleOrderAPIResponse:
    """Fetches sale orders using the provided API endpoint, with the filter by user_id."""

    session_id = redis_client.get("session_id")
    if not session_id:
        return ErrorResponse(jsonrpc="2.0", id=None, error=ErrorData(code=100, message="No session_id available. Please log in first."))

    # Prepare the base URL
    url = "http://0.0.0.0:8069/api/model/sale.order"

    # Add user_id filter if provided
    if user_id is not None:
        url += f"/?filter=[('user_id', '=', {user_id})]"

    headers = {
        "Content-Type": "application/json",
        "Cookie": f"session_id={session_id}"
    }
    data = {}
    print("----reque-----", url, headers, data)
    response = requests.get(url, headers=headers, json=data)
    print("----resp----", response.__dict__)
    response_data = response.json()

    # If there's an error in the response, return it
    if 'error' in response_data:
        redis_client.set("session_expired", int(True)
                         )  # Mark session as expired
        return ErrorResponse(**response_data)

    redis_client.set("session_expired", int(False))
    # If successful, return the sale order data
    return SaleOrderAPIResponse(**response_data)


class User(BaseModel):
    id: int
    name: str
    user_ids: List[int]


class UserData(BaseModel):
    current: int
    total_pages: int
    length_record: int
    record: List[User]


class UserResponse(BaseModel):
    status_code: int
    message: str
    data: UserData


class UserAPIResponse(BaseModel):
    jsonrpc: str
    id: Optional[int]
    result: Optional[UserResponse]
    success: Optional[bool] = None


class ErrorData(BaseModel):
    code: int
    message: str


class ErrorResponse(BaseModel):
    jsonrpc: str
    id: Optional[int]
    error: ErrorData


@tool
def fetch_user_id_by_login(session_id: str, login: str) -> UserAPIResponse:
    """Fetches user ID and name using the provided API endpoint, filtered by login field."""

    session_id = redis_client.get("session_id")
    if not session_id:
        return ErrorResponse(jsonrpc="2.0", id=None, error=ErrorData(code=100, message="No session_id available. Please log in first."))

    # Prepare the URL with the login filter
    url = f"http://0.0.0.0:8069/api/model/res.users/?fields=name%2Cuser_ids&filter=[('login', '=', '{login}')]"

    headers = {
        "Content-Type": "application/json",
        "Cookie": f"session_id={session_id}"
    }
    data = {}
    print("----reque-----", url, headers, data)
    response = requests.get(url, headers=headers, json=data)
    print("----resp----", response.__dict__)
    response_data = response.json()

    # If there's an error in the response, return it
    if 'error' in response_data:
        redis_client.set("session_expired", int(True)
                         )  # Mark session as expired
        return ErrorResponse(**response_data)

    redis_client.set("session_expired", int(False))
    # If successful, return the user data
    return UserAPIResponse(**response_data)
