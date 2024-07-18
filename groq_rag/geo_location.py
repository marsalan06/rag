from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits.openapi import planner
from langchain_community.agent_toolkits.openapi.spec import reduce_openapi_spec
from langchain.requests import RequestsWrapper
import requests
import yaml


class GeolocationAPI:
    def __init__(self, api_spec_url, api_key, base_url="https://ipgeolocation.abstractapi.com/v1/", save_to_file=False):
        """
        Initializes the GeolocationAPI class with the API specification URL, API key, and base URL.

        Parameters:
        - api_spec_url (str): URL to the OpenAPI specification.
        - api_key (str): API key for authentication.
        - base_url (str): Base URL for the API.
        - save_to_file (bool): Flag to save the YAML spec to a file or not (default: False).
        """
        self.api_spec_url = api_spec_url
        self.api_key = api_key
        self.base_url = base_url
        self.save_to_file = save_to_file
        self.api_spec = self.load_api_spec()
        # headers={"Authorization":f"Bearer <token>"}
        self.requests_wrapper = RequestsWrapper()
        self.llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.0)

    def load_api_spec(self):
        """
        Loads and reduces the OpenAPI specification from the provided URL.

        Returns:
        - dict: Reduced OpenAPI specification.
        """
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
            return reduce_openapi_spec(raw_spec)
        else:
            raise Exception("Failed to fetch API specification")

    def create_agent(self, allow_dangerous_requests=True):
        """
        Creates an OpenAPI agent for interacting with the API.

        Parameters:
        - allow_dangerous_requests (bool): Flag to enable dangerous requests (default: True).

        Returns:
        - Agent: An agent for making API calls.
        """
        return planner.create_openapi_agent(
            self.api_spec, self.requests_wrapper, self.llm, allow_dangerous_requests=allow_dangerous_requests
        )

    def get_ip_geolocation(self, ip_address=None, fields=None):
        """
        Retrieves the geolocation for a specific IP address using the API.

        Parameters:
        - ip_address (str): IP address to retrieve geolocation for (optional).
        - fields (str): Specific fields to retrieve (optional).

        Returns:
        - dict: The geolocation information.
        """
        params = {
            'api_key': self.api_key,
            'ip_address': ip_address,
            'fields': fields
        }

        # Creating the agent
        agent = self.create_agent()

        # Building the user query
        user_query = f"Retrieve the geolocation for IP address {ip_address} with fields {fields}. and api_key {self.api_key}"

        # Invoking the agent with the query
        response = agent.invoke(user_query)

        return response


# Example usage:
# Replace with actual OpenAPI spec URL
api_spec_url = "https://api.apis.guru/v2/specs/abstractapi.com/geolocation/1.0.0/openapi.yaml"
api_key = "---cl"  # Replace with your actual API key

# Instantiate the GeolocationAPI class
geolocation_api = GeolocationAPI(api_spec_url, api_key, save_to_file=False)

# Retrieve and print geolocation information for a specific IP address
ip_geolocation = geolocation_api.get_ip_geolocation(
    ip_address="195.154.25.40", fields="country,city,timezone")
print(ip_geolocation)  # Outputs the geolocation information
