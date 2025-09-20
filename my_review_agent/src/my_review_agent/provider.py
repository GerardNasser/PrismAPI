from typing import List, Dict, Any
from time import sleep
from Bio import Entrez as ez
import pandas as pd
import json
import xmltodict

from .client import NcbiClient, WosClient
from .models import PubMedArticle, WosArticle

class NcbiProvider:
    """
    The high-level provider for NCBI.
    It uses the NcbiClient to perform complex, multi-step operations.
    """
    def __init__(self, client: NcbiClient):
        self._client = client

    def _search_and_get_ids(self, db: str, term: str) -> Dict[str, Any] | None:
        """Helper function to perform a search and return history server details."""
        try:
            search_results = self._client.esearch(db=db, term=term)
            count = int(search_results["Count"])
            print(f"Provider: Found {count} results.")
            if count == 0:
                return {"count": 0}
            return {"count": count, "webenv": search_results["WebEnv"], "query_key": search_results["QueryKey"], "ids": search_results["IdList"]}
        except Exception as e:
            print(f"Provider: An error occurred during search: {e}")
            return None

    def get_summaries(self, db: str, term: str) -> List[Dict[str, Any]] | None:
        """Gets summaries for a search term."""
        search_info = self._search_and_get_ids(db, term)
        if not search_info or search_info["count"] == 0:
            return []
        try:
            summary_data = self._client.esummary(db=db, webenv=search_info['webenv'], query_key=search_info['query_key'])
            return summary_data
        except Exception as e:
            print(f"Provider: Could not fetch summaries. Error: {e}")
            return None

    def fetch_full_records(self, db: str, term: str) -> List[Any] | None:
        """Performs the complete search, fetch, and parse workflow for full records."""
        search_info = self._search_and_get_ids(db, term)
        if not search_info or search_info["count"] == 0:
            return []
        try:
            count, webenv, query_key = search_info['count'], search_info['webenv'], search_info['query_key']
            batch_size = 100
            all_records = []
            for start in range(0, count, batch_size):
                fetch_handle = self._client.efetch(db=db, webenv=webenv, query_key=query_key, retstart=start, retmax=batch_size)
                data = fetch_handle.read()
                fetch_handle.close()
                records = xmltodict.parse(data)
                all_records.append(records)
                sleep(0.3)
            print("Provider: Finished fetching all records.")
            if db.lower() == 'pubmed':
                return self._parse_pubmed_articles(all_records)
            else:
                print("Provider: Returning raw dictionary data for non-PubMed database.")
                return all_records
        except Exception as e:
            print(f"Provider: An error occurred during the fetch process: {e}")
            return None

    def find_and_link(self, source_db: str, source_term: str, target_db: str) -> List[Dict[str, Any]] | None:
        """Searches one database, then finds related items in another."""
        print(f"Provider: Initiating link from '{source_db}' to '{target_db}' for term '{source_term}'.")
        search_info = self._search_and_get_ids(source_db, source_term)
        if not search_info or search_info["count"] == 0: return []
        try:
            id_list = search_info['ids']
            linked_data = self._client.elink(db=target_db, dbfrom=source_db, id_list=id_list)
            final_links = []
            for record in linked_data:
                if 'LinkSetDb' in record and record['LinkSetDb']:
                    for link in record['LinkSetDb'][0]['Link']:
                        final_links.append({'SourceID': record['IdList'][0], 'TargetID': link['Id']})
            print(f"Provider: Found {len(final_links)} links.")
            return final_links
        except Exception as e:
            print(f"Provider: An error occurred during the linking process: {e}")
            return None

    def save_results_to_file(self, data: List[Any], filename: str) -> bool:
        """Saves a list of data (models or dicts) to a file."""
        if not data:
            print("Provider: No data to save.")
            return True
        try:
            if hasattr(data[0], 'model_dump'): data_dicts = [item.model_dump() for item in data]
            else: data_dicts = data
            if filename.lower().endswith(".csv"):
                pd.DataFrame(data_dicts).to_csv(filename, index=False)
            elif filename.lower().endswith(".json"):
                with open(filename, 'w') as f: json.dump(data_dicts, f, indent=4)
            else:
                print(f"Provider: Error: Unsupported file type for '{filename}'. Use .csv or .json.")
                return False
            print(f"Provider: Successfully saved {len(data)} records to {filename}")
            return True
        except Exception as e:
            print(f"Provider: Failed to save file '{filename}'. Error: {e}")
            return False

    def _parse_pubmed_articles(self, raw_records: List[Dict]) -> List[PubMedArticle]:
        """Specific parser for the detailed PubMed article structure returned by efetch."""
        parsed_articles = []
        articles_root = raw_records[0].get('PubmedArticleSet', {}).get('PubmedArticle', [])
        if not isinstance(articles_root, list): articles_root = [articles_root]
        for article_data in articles_root:
            citation = article_data.get('MedlineCitation', {})
            article_info = citation.get('Article', {})
            title = article_info.get('ArticleTitle', 'No Title Found')
            if isinstance(title, dict): title = title.get('#text', 'No Title Found')
            abstract_parts = article_info.get('Abstract', {}).get('AbstractText', [])
            if isinstance(abstract_parts, list): abstract = ' '.join(part.get('#text', '') if isinstance(part, dict) else part for part in abstract_parts)
            elif isinstance(abstract_parts, dict): abstract = abstract_parts.get('#text', 'No Abstract Found')
            else: abstract = abstract_parts or 'No Abstract Found'
            journal_info = article_info.get('Journal', {})
            journal_name = journal_info.get('Title', 'No Journal Found')
            pub_date = journal_info.get('JournalIssue', {}).get('PubDate', {})
            year = pub_date.get('Year', pub_date.get('MedlineDate', 'No Year Found'))
            pmid = citation.get('PMID', {}).get('#text', '')
            parsed_articles.append(PubMedArticle(PMID=str(pmid), Title=title, Abstract=abstract, Journal=journal_name, Year=str(year)))
        print(f"Provider: Successfully parsed {len(parsed_articles)} PubMed articles.")
        return parsed_articles

class WosProvider:
    """
    The high-level provider for Web of Science.
    """
    def __init__(self, client: WosClient):
        self._client = client

    def search_and_fetch(self, term: str) -> List[WosArticle] | None:
        """Fetches and parses results from the Web of Science API."""
        all_results = []
        # Max pages to fetch to avoid very long runs
        MAX_PAGES = 5
        try:
            for i in range(1, MAX_PAGES + 1):
                response = self._client.search(term=term, page=i)
                if response.status_code == 200:
                    data = response.json()
                    page_hits = data.get('hits', [])
                    if page_hits:
                        all_results.extend(page_hits)
                        print(f"WOS Provider: ... Success! Added {len(page_hits)} results from page {i}.")
                    else:
                        print("WOS Provider: ... No more results found. Stopping.")
                        break
                else:
                    print(f"WOS Provider: ... Error on page {i}: Status code {response.status_code}")
                    print(f"WOS Provider: ... Response: {response.text}")
                    break # Stop on error
            
            return self._parse_wos_articles(all_results)
        except Exception as e:
            print(f"WOS Provider: An error occurred during fetch: {e}")
            return None

    def save_results_to_file(self, data: List[Any], filename: str) -> bool:
        """Saves a list of data (models or dicts) to a file."""
        if not data:
            print("Provider: No data to save.")
            return True
        try:
            if hasattr(data[0], 'model_dump'): data_dicts = [item.model_dump() for item in data]
            else: data_dicts = data
            if filename.lower().endswith(".csv"):
                pd.DataFrame(data_dicts).to_csv(filename, index=False)
            elif filename.lower().endswith(".json"):
                with open(filename, 'w') as f: json.dump(data_dicts, f, indent=4)
            else:
                print(f"Provider: Error: Unsupported file type for '{filename}'. Use .csv or .json.")
                return False
            print(f"Provider: Successfully saved {len(data)} records to {filename}")
            return True
        except Exception as e:
            print(f"Provider: Failed to save file '{filename}'. Error: {e}")
            return False

    def _parse_wos_articles(self, raw_records: List[Dict]) -> List[WosArticle]:
        """Parses the raw JSON from WoS into a list of WosArticle models."""
        publication_list = []
        for record in raw_records:
            source_info = record.get('source', {})
            names_info = record.get('names', {})
            authors_list = names_info.get('authors', [])
            if authors_list:
                author_names = [author.get('displayName') for author in authors_list if author]
                authors_str = '; '.join(author_names)
            else:
                authors_str = 'N/A'
            
            processed_record = WosArticle(
                UID=record.get('uid', 'N/A'),
                DOI=record.get('identifiers', {}).get('doi', 'N/A'),
                Title=record.get('title', 'N/A').lower(),
                Year=source_info.get('publishYear', 'N/A'),
                Journal=source_info.get('sourceTitle', 'N/A'),
                Authors=authors_str
            )
            publication_list.append(processed_record)
        
        print(f"WOS Provider: Successfully parsed {len(publication_list)} articles.")
        return publication_list