from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits.openapi import planner
from langchain_community.agent_toolkits.openapi.spec import reduce_openapi_spec
from langchain.requests import RequestsWrapper
import requests
import yaml
import os

os.environ['OPENAI_API_KEY'] = "sk-proj-"


class GenericAPIClient:
    def __init__(self, api_spec_url=None, api_spec_file=None, api_key=None, base_url=None, save_to_file=False):
        """
        Initializes the GenericAPIClient class with the API specification URL or file, optional API key, and optional base URL.

        Parameters:
        - api_spec_url (str): URL to the OpenAPI specification (optional).
        - api_spec_file (str): Path to the local OpenAPI specification YAML file (optional).
        - api_key (str): API key for authentication (optional).
        - base_url (str): Base URL for the API (optional).
        - save_to_file (bool): Flag to save the YAML spec to a file or not (default: False).
        """
        self.api_spec_url = api_spec_url
        self.api_spec_file = api_spec_file
        self.api_key = api_key
        self.base_url = base_url
        self.save_to_file = save_to_file
        self.api_spec = self.load_api_spec()
        # self.requests_wrapper = RequestsWrapper(
        #     headers=self.construct_headers())
        self.requests_wrapper = RequestsWrapper()
        self.llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.5)

    def load_api_spec(self):
        """
        Loads and reduces the OpenAPI specification from the provided URL or file.

        Returns:
        - dict: Reduced OpenAPI specification.
        """
        if self.api_spec_file and os.path.exists(self.api_spec_file):
            with open(self.api_spec_file, "r", encoding='utf-8') as file:
                raw_spec = yaml.safe_load(file)
        elif self.api_spec_url:
            response = requests.get(self.api_spec_url)
            response.encoding = 'utf-8'  # Ensure the response is decoded as UTF-8
            if response.status_code == 200:
                if self.save_to_file:
                    with open("api_spec.yaml", "w", encoding='utf-8') as file:
                        file.write(response.text)
                    with open("api_spec.yaml", "r", encoding='utf-8') as file:
                        raw_spec = yaml.safe_load(file)
                else:
                    raw_spec = yaml.safe_load(response.text)
            else:
                raise Exception("Failed to fetch API specification from URL")
        else:
            raise ValueError(
                "Either api_spec_url or api_spec_file must be provided")
        print("------here-----", raw_spec)
        return reduce_openapi_spec(raw_spec)

    def construct_headers(self):
        """
        Constructs headers for the RequestsWrapper, including the API key if provided.

        Returns:
        - dict: Headers for the RequestsWrapper.
        """
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def create_agent(self, allow_dangerous_requests=True):
        """
        Creates an OpenAPI agent for interacting with the API.

        Parameters:
        - allow_dangerous_requests (bool): Flag to enable dangerous requests (default: True).

        Returns:
        - Agent: An agent for making API calls.
        """
        return planner.create_openapi_agent(
            self.api_spec, self.requests_wrapper, self.llm, allow_dangerous_requests=allow_dangerous_requests, handle_parsing_errors=True
        )

    def invoke_api(self, user_query):
        """
        Invokes the API using the agent based on the user query.

        Parameters:
        - user_query (str): The query to pass to the agent.

        Returns:
        - dict: The response from the API.
        """
        agent = self.create_agent()
        response = agent.invoke(user_query)
        return response


# Example usage:
# Replace with actual OpenAPI spec URL or file path
# api_spec_url = "https://api.apis.guru/v2/specs/abstractapi.com/geolocation/1.0.0/openapi.yaml"
api_spec_url = None
# "path/to/local/api_spec.yaml"  # Replace with the path to the local YAML file if available
api_spec_file = 'nobel_api.yaml'
# Replace with your actual API key (optional)
api_key = "94feedc10bb3403ca158b2e1acdc57b4"

# Instantiate the GenericAPIClient class
api_client = GenericAPIClient(
    api_spec_url=api_spec_url, api_spec_file=api_spec_file, save_to_file=False)

# Define a user query to interact with the API
user_query = "Retrieve the top 10 Nobel Prizes in ascending order."

# Invoke the API and print the response
response = api_client.invoke_api(user_query)
print(response)  # Outputs the API response
