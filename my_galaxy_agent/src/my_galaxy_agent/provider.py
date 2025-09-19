from typing import List
from pydantic import ValidationError
from requests.exceptions import RequestException

from .models import DataLibrary, History, Workflow, Tool # <-- Import Tool
from .client import GalaxyApiClient

class GalaxyProvider:
    def __init__(self, client: GalaxyApiClient):
        self._client = client

    # CORRECTED: This method is now simpler and more efficient.
    def fetch_all_libraries(self) -> List[DataLibrary] | None:
        """ Fetches all Data Libraries from Galaxy. """
        print("Provider: Requesting Data Library list from the client...")
        try:
            response = self._client.get_libraries()
            response.raise_for_status()
            # Directly validate the JSON list into your Pydantic models
            return [DataLibrary.model_validate(item) for item in response.json()]
        except (RequestException, ValidationError) as e:
            print(f"Error fetching libraries: {e}")
            return None

    def fetch_all_histories_with_details(self) -> List[History] | None:
        """ Fetches all Histories and enriches them with details. """
        print("Provider: Requesting initial Data History list from the client...")
        try:
            list_response = self._client.get_histories()
            list_response.raise_for_status()
            detailed_histories: List[History] = []
            for summary in list_response.json():
                details_response = self._client.show_history(history_id=summary['id'])
                details_response.raise_for_status()
                detailed_histories.append(History.model_validate(details_response.json()))
            return detailed_histories
        except (RequestException, ValidationError) as e:
            print(f"Error fetching histories: {e}")
            return None

    def fetch_all_workflows(self) -> List[Workflow] | None:
        """ Fetches all Workflows from Galaxy and validates the response. """
        try:
            response = self._client.get_workflows()
            response.raise_for_status()
            return [Workflow.model_validate(item) for item in response.json()]
        except (RequestException, ValidationError) as e:
            print(f"Error fetching workflows: {e}")
            return None

    def fetch_all_tools(self) -> List[Tool] | None:
        """ Fetches all Tools from Galaxy and validates the response. """
        try:
            response = self._client.get_tools()
            response.raise_for_status()
            return [Tool.model_validate(item) for item in response.json()]
        except (RequestException, ValidationError) as e:
            print(f"Error fetching tools: {e}")
            return None