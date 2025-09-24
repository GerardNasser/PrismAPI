import requests
from typing import Dict, Any
from Bio import Entrez as ez
from time import sleep
from urllib.parse import quote, urlencode

# ==============================================================================
# NCBI CLIENT
# ==============================================================================
class NcbiClient:
    """The low-level client for the NCBI Entrez API."""
    def __init__(self, email: str, api_key: str | None = None):
        ez.email = email
        if api_key:
            ez.api_key = api_key

    def esearch(self, db: str, term: str) -> Dict[str, Any]:
        """Performs an esearch to find IDs for a given term."""
        print(f"NCBI Client: Performing esearch in '{db}' for term '{term}'...")
        handle = ez.esearch(db=db, term=term, usehistory="y")
        results = ez.read(handle)
        handle.close()
        return results

    def efetch(self, db: str, webenv: str, query_key: str, retstart: int, retmax: int) -> Any:
        """Performs an efetch to retrieve full records in batches."""
        print(f"NCBI Client: Fetching records {retstart+1}-{retstart+retmax}...")
        handle = ez.efetch(db=db, webenv=webenv, query_key=query_key, retstart=retstart, retmax=retmax, rettype="xml", retmode="xml")
        records = ez.read(handle)
        handle.close()
        return records

    def esummary(self, db: str, webenv: str, query_key: str, retstart: int, retmax: int) -> Any:
        """Performs an esummary to retrieve brief summaries."""
        print(f"NCBI Client: Fetching summaries {retstart+1}-{retstart+retmax}...")
        handle = ez.esummary(db=db, webenv=webenv, query_key=query_key, retstart=retstart, retmax=retmax)
        records = ez.read(handle)
        handle.close()
        return records

    def elink(self, source_db: str, target_db: str, id_list: list) -> Any:
        """Performs an elink to find related records in another database."""
        print(f"NCBI Client: Linking {len(id_list)} IDs from '{source_db}' to '{target_db}'...")
        handle = ez.elink(dbfrom=source_db, db=target_db, id=id_list)
        links = ez.read(handle)
        handle.close()
        return links

# ==============================================================================
# WEB OF SCIENCE (WOS) STARTER CLIENT
# ==============================================================================
class WosStarterClient:
    """The low-level client for the Web of Science STARTER API."""
    def __init__(self, api_key: str, base_url: str):
        if not api_key:
            raise ValueError("Web of Science API key is required.")
        if not base_url:
            raise ValueError("Web of Science Base URL is required.")
        self._api_key = api_key
        self._base_url = base_url
        self._headers = {'accept': 'application/json', 'X-ApiKey': self._api_key}

    def search(self, term: str, page: int, limit: int, db: str, sort_field: str) -> Dict[str, Any]:
        """Performs a search against the configured WOS API endpoint."""
        # 1. Prepare the main query string value.
        # ADD A WAY TO PUT TS=AFTER EVERY BOOLEAN THAT IS NOT WITHING A PARENTHESIS
        formatted_term = f"({term})"
        query_value = f"TS={formatted_term}"

        # 2. Prepare the other parameters, now using arguments.
        other_params = {
            'db': db,
            'limit': limit,
            'page': page,
            'sortField': sort_field
        }

        # 3. Encode the other parameters. This correctly handles sortField.
        encoded_other_params = urlencode(other_params)

        # 4. Encode the main query value separately. quote() uses '%20' for spaces.
        encoded_q_value = quote(query_value)

        # 5. Manually construct the final URL with each part encoded correctly.
        full_url = f"{self._base_url}?q={encoded_q_value}&{encoded_other_params}"
        
        print(f"WOS Client: Requesting page {page} for term '{term}'...")
        print(f"WOS Client: Final URL: {full_url}")
        
        # Pass the fully constructed URL directly.
        response = requests.get(full_url, headers=self._headers)
        response.raise_for_status()
        return response.json()