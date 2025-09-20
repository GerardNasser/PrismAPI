from pydantic import BaseModel, Field
from typing import List

class PubMedArticle(BaseModel):
    """
    Represents a single, parsed article from a PubMed search.
    This model guarantees that every article in our application
    has these specific fields.
    """
    PMID: str
    Title: str
    Abstract: str
    Journal: str
    Year: str

class WosArticle(BaseModel):
    """
    Represents a single, parsed article from a Web of Science search.
    """
    UID: str
    DOI: str
    Title: str
    Year: str | int
    Journal: str
    Authors: str