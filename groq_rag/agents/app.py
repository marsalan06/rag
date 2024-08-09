import streamlit as st
from dataclasses import dataclass
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from api_collection import fetch_finance_logo, store_user_credentials, login_to_odoo, fetch_sale_orders, fetch_sale_orders_by_user_id, check_session_status, fetch_user_id_by_login, SaleOrderAPIResponse, FinanceLogoResponse, ErrorResponse, UserAPIResponse, SaleOrder
from pydantic import BaseModel, Field
from weather_api import fetch_current_weather, WeatherAPIResponse
from xml_odoo_tools import xmlrpc_login_to_odoo, xmlrpc_fetch_sale_orders_by_user_id
from typing import Optional, List, Dict
import os


# Set environment variables for API keys and LangChain configuration
os.environ['OPENAI_API_KEY'] = "sk-proj-"
os.environ['LANGCHAIN_TRACING_V2'] = 'true'
os.environ['LANGCHAIN_ENDPOINT'] = 'https://api.smith.langchain.com'
os.environ['LANGCHAIN_API_KEY'] = ''

# Define a Message data class to structure chat messages with actor and payload


@dataclass
class Message:
    actor: str
    payload: str


# Define constants for the roles in the chat
USER = "user"
ASSISTANT = "ai"
MESSAGES = "messages"

# Function to initialize session state variables


def initialize_session_state():
    # Initialize the message history if it doesn't exist in session state
    if MESSAGES not in st.session_state:
        st.session_state[MESSAGES] = [
            Message(actor=ASSISTANT, payload="Hi! How can I help you?")]

    # Initialize the agent executor if it doesn't exist in session state
    if "agent_executor" not in st.session_state:
        st.session_state["agent_executor"] = get_agent_executor()

# Function to create the agent executor, which handles the interaction logic


def get_agent_executor() -> AgentExecutor:
    # Define the chat prompt template used to guide the conversation
    prompt = ChatPromptTemplate.from_messages([
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
         "Always ensure that the correct tool is used based on the query, managing sessions, user IDs, and other data as needed."),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}")
    ])

    # "You are a helpful assistant. You have access to multiple APIs, including Odoo APIs and others. "
    #                    "When interacting with Odoo APIs, you must manage a session ID. "
    #                    "If the session ID is available and not expired, don't call the login API every time; use it to call the Odoo sales API or any other Odoo-specific API. "
    #                    "If the session has expired or is not available, first call the login API to obtain a new session ID, "
    #                    "and then proceed with the Odoo API request. For non-Odoo APIs, you do not need to handle the session ID."
    #                    "When a user wants sale orders, determine the wether they provide a user id or not from their query. "
    #                    "If their is a user_id pass it to the 'fetch_sale_orders_by_user_id' tool."
    #                    "If user has provided their login id/name use the 'fetch_user_id_by_login' to get the user_id and then use 'fetch_sale_orders_by_user_id' "

    # Define the tools that the agent can use (e.g., API calls)
    tools = [check_session_status, store_user_credentials, fetch_current_weather,
             fetch_finance_logo, xmlrpc_login_to_odoo, xmlrpc_fetch_sale_orders_by_user_id]

    # Define the language model used by the agent
    llm = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0)

    # Create the tool-calling agent with the prompt, language model, and tools
    agent = create_tool_calling_agent(llm, tools, prompt)

    # Wrap the agent in an executor, which manages the interaction loop
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    return agent_executor

# Helper function to extract text or summary information from different response types


def extract_text_from_response(response) -> str:
    if isinstance(response, WeatherAPIResponse):
        location = response.location.name
        description = response.current.condition.text
        temperature = response.current.temp_c
        return f"Weather in {location}: {description}, Temperature: {temperature}°C"

    elif isinstance(response, SaleOrderAPIResponse):
        if response.success:
            orders = response.result.data.record
            return f"Found {len(orders)} sale orders: " + ", ".join([order.name for order in orders])
        else:
            return f"Error: {response.result.message}"

    elif isinstance(response, list) and all(isinstance(order, SaleOrder) for order in response):
        # Handle a list of SaleOrder objects from XML-RPC response
        if response:
            return f"Found {len(response)} sale orders: " + ", ".join([order.name for order in response])
        else:
            return "No sale orders found."

    elif isinstance(response, FinanceLogoResponse):
        return f"Logo URL: {response.logo}" if response.logo else "No logo found for the specified stock."

    elif isinstance(response, UserAPIResponse):
        if response.success:
            users = response.result.data.record
            return f"Found {len(users)} users: " + ", ".join([user.name for user in users])
        else:
            return f"Error: {response.result.message}"

    elif isinstance(response, ErrorResponse):
        return f"Error: {response.error.message} (Code: {response.error.code})"

    else:
        try:
            return str(response['output'])
        except Exception as e:
            return f"Received an unrecognized response format. Error: {str(e)}"


# Initialize the session state variables
initialize_session_state()

# Display existing messages from the session state in the chat UI
msg: Message
for msg in st.session_state[MESSAGES]:
    st.chat_message(msg.actor).write(msg.payload)

# Capture user input from the chat input widget
prompt: str = st.chat_input("Enter a prompt here")

# If the user provides a prompt, process it
if prompt:
    # Append the user's message to the session state message history
    st.session_state[MESSAGES].append(Message(actor=USER, payload=prompt))
    st.chat_message(USER).write(prompt)

    # Show a spinner while the agent is processing the user's input
    with st.spinner("Please wait.."):
        # Retrieve the agent executor from the session state
        agent_executor = st.session_state["agent_executor"]

        # Use the agent executor to process the input and get a response
        response = agent_executor.invoke({"input": prompt})

        # Extract the necessary information from the response using the helper function
        response_text = extract_text_from_response(response)

        # Append the agent's response to the session state message history
        st.session_state[MESSAGES].append(
            Message(actor=ASSISTANT, payload=response_text))

        # Display the agent's response in the chat UI
        st.chat_message(ASSISTANT).write(response_text)
