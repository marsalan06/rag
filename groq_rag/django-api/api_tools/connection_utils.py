
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import os
from langchain.memory.simple import SimpleMemory
import redis


redis_client = redis.StrictRedis(
    host='172.17.0.2', port=6379, db=0, decode_responses=True)
redis_client.set("session_expired", int(False))  # Store as 0


# Initialize memory to store session_id
memory = SimpleMemory(memories={
    # Initially, set to True to ensure login is called first
    "db": "postgres",
    "username": "",
    "password": ""
})

# chat_setup.py


# Set environment variables for API keys and LangChain configuration
os.environ['OPENAI_API_KEY'] = "sk-proj-"
os.environ['LANGCHAIN_TRACING_V2'] = 'true'
os.environ['LANGCHAIN_ENDPOINT'] = 'https://api.smith.langchain.com'
os.environ['LANGCHAIN_API_KEY'] = ''


def get_chat_openai():
    return ChatOpenAI(model="gpt-4o-mini", temperature=0)


def get_chat_prompt():
    return ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant with access to multiple APIs, including Odoo APIs and others. "
         "When interacting with Odoo APIs, you must manage user authentication. "
         "Check if the session is valid by using the 'check_session_status' tool, which returns a dict with status. "
         "If the session is valid (True), proceed to use the Odoo APIs without re-authenticating. "
         "If the session is not valid (False), first call the 'xmlrpc_login_to_odoo' tool to authenticate the user and obtain the 'user_id'. "
         "Store the 'user_id' and then proceed with the Odoo API request using this 'user_id'. "
         "When a user requests sale orders, determine whether they provide a user ID or if you need to use the stored 'user_id' from the login process. "
         "If there is no user_id or user_name use the store_user_credentials tool to store the user_name and password in memory"
         "Use the 'xmlrpc_fetch_sale_orders_by_user_id' tool to fetch sale orders associated with the user. "
         "For weather information, use the 'fetch_current_weather' tool. "
         "For stock logos, use the 'fetch_finance_logo' tool. "
         "Always ensure that the correct tool is used based on the query, managing sessions, user IDs, and other data as needed."
         "Return only a fixed json structure and add a place holder key value field in the response for the type of tool user example tool_type:weather or tool_type:sale_order"
         "Dont add anything else"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}")
    ])
