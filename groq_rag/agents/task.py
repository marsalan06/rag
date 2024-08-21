from crewai import Crew, Process
from crewai import Task
from crewai import Agent, Task, Crew, Process
import xml_odoo_tools as odoo_tools

search_tool = odoo_tools.xmlrpc_fetch_sale_orders_by_user_id
create_order_tool = odoo_tools.xmlrpc_create_sale_order

authenticator = Agent(
    role='Odoo Authenticator',
    goal='Authenticate with Odoo using XML-RPC and store session details.',
    backstory="Handles authentication to ensure other tasks can proceed.",
    tools=[odoo_tools.xmlrpc_login_to_odoo],
    verbose=True
)

researcher = Agent(
    role='Odoo Data Analyst',
    goal='Analyze sales data in Odoo.',
    backstory="Responsible for extracting and analyzing sales orders.",
    tools=[search_tool],
    verbose=True
)

creator = Agent(
    role='Odoo Sales Order Creator',
    goal='Create new sales orders in Odoo.',
    backstory="Handles the creation of sales orders.",
    tools=[create_order_tool],
    verbose=True
)


# Task for logging in
login_task = Task(
    description="Log in to Odoo using XML-RPC and retrieve user ID.",
    expected_output="User ID and session stored in Redis.",
    agent=authenticator
)

# Task for fetching sale orders
fetch_task = Task(
    description="Fetch and analyze sales orders.",
    expected_output="List of analyzed sales orders.",
    agent=researcher
)

# Task for creating sale orders
create_task = Task(
    description="Create a new sales order for a specific customer.",
    expected_output="Sales order ID for the newly created order.",
    agent=creator
)


crew = Crew(
    agents=[authenticator, researcher, creator],
    tasks=[login_task, fetch_task, create_task],
    process=Process.sequential  # Ensures tasks are executed in order
)

# Run the crew and print the result
result = crew.kickoff()
print(result)
