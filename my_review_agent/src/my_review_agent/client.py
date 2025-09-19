from requests import Response
from uplink import Consumer, get, headers

@headers({"Accept": "application/json"})
class GalaxyApiClient(Consumer):
    """The low-level client for the Galaxy API."""

    def __init__(self, base_url: str, api_key: str):
        super().__init__(base_url=base_url)
        # Set the API key as a header for all requests made by this client
        self.session.headers["x-api-key"] = api_key

    @get("/api/histories")
    def get_histories(self) -> Response: # type: ignore
        """Performs a GET request to the /api/histories endpoint."""
        pass