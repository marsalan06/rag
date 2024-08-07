from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from api_collection import fetch_weather, fetch_finance_logo, login_to_odoo, check_session_status, fetch_sale_orders
from weather_api import fetch_current_weather
import re
import os

os.environ['OPENAI_API_KEY'] = "sk-proj-"
os.environ['LANGCHAIN_TRACING_V2'] = 'true'
os.environ['LANGCHAIN_ENDPOINT'] = 'https://api.smith.langchain.com'
os.environ['LANGCHAIN_API_KEY'] = ''

# Define the chat prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant. You have access to multiple APIs, including Odoo APIs and others. "
     "When interacting with Odoo APIs, you must manage a session ID. "
     "If the session ID is available and not expired, don't call the login API every time; use it to call the Odoo sales API or any other Odoo-specific API. "
     "If the session has expired or is not available, first call the login API to obtain a new session ID, "
     "and then proceed with the Odoo API request. For non-Odoo APIs, you do not need to handle the session ID."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])

# Define the tools
tools = [check_session_status, fetch_current_weather,
         fetch_finance_logo, login_to_odoo, fetch_sale_orders]

# Define the language model
llm = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0)

# Create the tool-calling agent
agent = create_tool_calling_agent(llm, tools, prompt)

# Create the agent executor
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

input_message = "What is the logo of Amazon and what are my top sales for company 2?"
# input_message = "What is the weather in Karachi and show the sales for user_id=2 with fields user_id, name, and amount_total?"


response = agent_executor.invoke({"input": input_message})
print(response)
