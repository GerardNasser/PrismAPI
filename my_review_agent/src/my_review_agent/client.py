from Bio import Entrez as ez
from typing import Dict, Any, IO, List
import requests
import urllib.parse

class NcbiClient:
    """
    The low-level client for the NCBI Entrez API.
    This class directly wraps the Biopython Entrez functions.
    """
    def __init__(self, email: str, api_key: str | None = None):
        if not email:
            raise ValueError("NCBI Entrez requires an email address.")
        ez.email = email
        if api_key:
            ez.api_key = api_key

    def esearch(self, db: str, term: str) -> Dict[str, Any]:
        """Performs an esearch to find IDs for a given term in a database."""
        print(f"Client: Performing esearch in '{db}' for term '{term}'...")
        handle = ez.esearch(db=db, term=term, usehistory="y", idtype="acc")
        results = ez.read(handle)
        handle.close()
        return results

    def efetch(self, db: str, webenv: str, query_key: str, retstart: int, retmax: int) -> IO[str]:
        """Performs an efetch to retrieve full records in batches."""
        print(f"Client: Fetching records from {retstart+1} to {retstart+retmax}...")
        return ez.efetch(db=db, webenv=webenv, query_key=query_key, retstart=retstart, retmax=retmax, rettype="xml", retmode="xml")

    def esummary(self, db: str, webenv: str, query_key: str) -> Dict[str, Any]:
        """Performs an esummary to retrieve summary information for a set of records."""
        print(f"Client: Fetching summaries from '{db}'...")
        handle = ez.esummary(db=db, webenv=webenv, query_key=query_key)
        results = ez.read(handle)
        handle.close()
        return results

    def elink(self, db: str, dbfrom: str, id_list: List[str]) -> List[Dict[str, Any]]:
        """Performs an elink to find related records in another database."""
        print(f"Client: Linking from '{dbfrom}' to '{db}' for {len(id_list)} IDs...")
        handle = ez.elink(db=db, dbfrom=dbfrom, id=id_list, linkname=f"{dbfrom}_{db}")
        results = ez.read(handle)
        handle.close()
        return results

class WosClient:
    """
    The low-level client for the Web of Science Starter API.
    """
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Web of Science API requires an API key.")
        self._api_key = api_key
        self._base_url = "https://api.clarivate.com/api/wos/"

    def search(self, term: str, page: int) -> requests.Response:
        """Performs a search for a given term and page number."""
        print(f"WOS Client: Requesting page {page} for term '{term}'...")
        headers = {
            'accept': 'application/json',
            'X-ApiKey': self._api_key
        }
        # The WoS API requires a 'Topic Search' tag like TS=()
        search_phrase_with_tag = f'TS=({term})'
        params = {
            'db': 'WOS', # Core Collection
            'q': search_phrase_with_tag,
            'limit': 50, # Max allowed by starter API
            'page': page
        }
        return requests.get(self._base_url, headers=headers, params=params)

