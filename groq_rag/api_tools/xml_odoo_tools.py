import xmlrpc.client
from pydantic import BaseModel, Field
from typing import List, Tuple, Optional
from .api_collection import memory, redis_client, ErrorData, ErrorResponse, SaleOrder
from langchain_core.tools import tool


@tool
def xmlrpc_login_to_odoo() -> int:
    """Logs in to the Odoo API using XML-RPC and retrieves the user_id, storing it in Redis."""

    url = "http://0.0.0.0:8069"
    db = "postgres"

    # Retrieve username and password from memory
    username = memory.memories.get("username")
    password = memory.memories.get("password")
    print("----login creds======", username, password)

    if not username or not password:
        raise ValueError(
            "Username or password not found in memory. Please set them first.")

    # Authenticate the user
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    uid = common.authenticate(db, username, password, {})

    if not uid:
        raise ValueError(
            "Failed to authenticate user with the provided credentials.")

    # Store user_id and session information in Redis using the username as the key
    redis_client.hset(f"user_session_{username}", mapping={
                      "user_id": uid, "session_expired": "0"})

    # Optionally, store the current username in Redis for quick access
    print("----data set in redis------", uid, username)
    return uid


@tool
def xmlrpc_fetch_sale_orders_by_user_id() -> List[SaleOrder]:
    """Fetches sale orders for the authenticated user using XML-RPC, combining search and read in one operation."""

    url = "http://0.0.0.0:8069"
    db = "postgres"

    username = memory.memories.get("username")

    if not username:
        raise ErrorResponse(jsonrpc="2.0", id=None, error=ErrorData(
            code=100, message="Username not found in memory."))

    user_info = redis_client.hgetall(f"user_session_{username}")
    uid = user_info.get("user_id")

    # Retrieve password from SimpleMemory
    password = memory.memories.get("password")

    print("-----creds----", db, uid, password)

    if not uid:
        return ErrorResponse(jsonrpc="2.0", id=None, error=ErrorData(code=100, message="No user_id available. Please log in first."))

    # Connect to the object endpoint
    models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
    print("-----models-----", models)
    # Use search_read to combine search and read into one operation
    fields = ['name', 'id', 'date_order', 'amount_total']

    print("----user 0--sud---", uid, type(uid))
    sale_order_ids = models.execute_kw(db, uid, password, 'sale.order', 'search',
                                       [[['user_id', '=', int(uid)]]])  # Filter by user_id

    print("----sale order ids-----", sale_order_ids)

    # Fetch the sale orders based on the retrieved sale_order_ids
    result = models.execute_kw(db, uid, password, 'sale.order', 'read',
                               [sale_order_ids],
                               {'fields': ['id', 'name', 'state', 'date_order', 'amount_total', 'company_id', 'user_id']})

    print("----sales orders---", result)
    if not result:
        return ErrorResponse(jsonrpc="2.0", id=None, error=ErrorData(code=101, message="No sale orders found."))

    return [SaleOrder(**order) for order in result]


class CreateSaleOrderResponse(BaseModel):
    jsonrpc: str
    id: Optional[str]
    result: int


@tool
def xmlrpc_create_sale_order(partner_id: int, order_lines: List[Tuple[int, float]]) -> CreateSaleOrderResponse:
    """
    Creates a new sale order in Odoo with the specified partner ID and order lines using XML-RPC.

    Parameters:
    - partner_id: The ID of the customer for whom the sale order is created.
    - order_lines: A list of tuples where each tuple contains the product ID and quantity.
    """

    url = "http://0.0.0.0:8069"
    db = "postgres"

    username = memory.memories.get("username")

    if not username:
        raise ErrorResponse(jsonrpc="2.0", id=None, error=ErrorData(
            code=100, message="Username not found in memory."))

    user_info = redis_client.hgetall(f"user_session_{username}")
    uid = user_info.get("user_id")

    # Retrieve password from SimpleMemory
    password = memory.memories.get("password")

    print("-----creds----", db, uid, password)

    if not uid:
        return ErrorResponse(jsonrpc="2.0", id=None, error=ErrorData(code=100, message="No user_id available. Please log in first."))

    # Connect to the object endpoint
    models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
    print("-----models-----", models)

    # Prepare order line data
    order_line_data = []
    for product_id, quantity in order_lines:
        order_line_data.append((0, 0, {
            'product_id': product_id,
            'product_uom_qty': quantity,
            'price_unit': 100.0,  # Example price, replace with actual logic if needed
        }))

    # Create a new sale order
    sale_order_id = models.execute_kw(db, uid, password, 'sale.order', 'create', [{
        'partner_id': partner_id,
        'order_line': order_line_data,
    }])

    if not sale_order_id:
        return ErrorResponse(jsonrpc="2.0", id=None, error=ErrorData(code=103, message="Failed to create the sale order."))

    return CreateSaleOrderResponse(jsonrpc="2.0", id=None, result=sale_order_id)
