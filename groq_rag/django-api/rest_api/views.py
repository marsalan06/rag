# In your Django app's views.py
import json
from rest_framework.decorators import api_view, permission_classes
from rest_framework_api_key.permissions import HasAPIKey
from rest_framework.response import Response
from rest_framework import status
from typing import Any
from pydantic import BaseModel, Field
from api_tools import get_chat_openai, get_chat_prompt
from langchain.agents import create_tool_calling_agent, AgentExecutor
from api_tools import (
    check_session_status, store_user_credentials, fetch_current_weather,
    xmlrpc_login_to_odoo, xmlrpc_fetch_sale_orders_by_user_id
)
from .utils import SaleOrderResponse
# Initialize the agent_executor


def get_agent_executor() -> AgentExecutor:
    prompt = get_chat_prompt()
    tools = [check_session_status, store_user_credentials, fetch_current_weather,
             xmlrpc_login_to_odoo, xmlrpc_fetch_sale_orders_by_user_id]
    llm = get_chat_openai()
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    return agent_executor


@api_view(['POST'])
@permission_classes([HasAPIKey])
def process_query_view(request):
    query = request.data.get("query")
    if not query:
        return Response({"error": "Query text is required."}, status=status.HTTP_400_BAD_REQUEST)

    agent_executor = get_agent_executor()

    # Process the query using the agent_executor
    raw_response = agent_executor.invoke({"input": query})

    # Parse the raw response and map it to a Pydantic model
    try:
        print("-1-1-1-1--", raw_response["output"])
        pydantic_response = json.loads(raw_response["output"])
        print("----2-2-2--2-", pydantic_response)
    except (AttributeError, ValueError, TypeError) as e:
        return Response({"error": f"Failed to parse response: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Return the Pydantic model as a JSON response
    return Response(pydantic_response, status=status.HTTP_200_OK)
