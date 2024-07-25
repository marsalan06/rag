from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from api_collection import fetch_weather, fetch_finance_logo
import re
import os

os.environ['OPENAI_API_KEY'] = "sk-proj-"
os.environ['LANGCHAIN_TRACING_V2'] = 'true'
os.environ['LANGCHAIN_ENDPOINT'] = 'https://api.smith.langchain.com'
os.environ['LANGCHAIN_API_KEY'] = ''

# Define the chat prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", "You're a helpful assistant"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])

# Define the tools
tools = [fetch_weather, fetch_finance_logo]

# Define the language model
llm = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0)

# Create the tool-calling agent
agent = create_tool_calling_agent(llm, tools, prompt)

# Create the agent executor
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# Function to parse the input query and extract parameters


# def parse_query(input_query):
#     city_match = re.search(r"weather in ([\w\s]+)", input_query, re.IGNORECASE)
#     city = city_match.group(1) if city_match else None

#     stock_match = re.search(r"logo for ([\w\s]+)", input_query, re.IGNORECASE)
#     stock = stock_match.group(1) if stock_match else None

#     return city, stock


# Define the input message
# input_message = "What is the current weather in Karachi, give me result in centrigrade? Also, get me the logo for AMZN."
input_message = "Hey how are you ?"
# Parse the query to extract parameters
# city, stock = parse_query(input_message)

# Initialize the parameters dictionary
# params = {}

# # Add weather parameters if city is found
# if city:
#     params["fetch_weather"] = {"city": city}

# # Add finance logo parameters if stock is found
# if stock:
#     params["fetch_finance_logo"] = {"stock": stock}

# Execute the agent
response = agent_executor.invoke({"input": input_message})
print(response)