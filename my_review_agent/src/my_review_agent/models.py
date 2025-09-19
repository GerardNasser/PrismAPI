from pydantic import BaseModel

## PubMed Models
class ESearch(BaseModel):
    """
    Represents a single History from the Galaxy API.
    This ensures any history data we use has at least an id and a name.
    """
    id: str
    name: str
    # Add any other fields you expect from the API, like 'url', 'count', etc.s