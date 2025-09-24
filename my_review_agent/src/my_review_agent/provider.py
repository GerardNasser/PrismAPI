import pandas as pd
from time import sleep
from typing import List
from requests.exceptions import HTTPError

from .client import NcbiClient, WosStarterClient
from .models import PubMedArticle, WosArticle

# ==============================================================================
# NCBI PROVIDER
# ==============================================================================
class NcbiProvider:
    """The high-level provider for NCBI search workflows."""
    def __init__(self, client: NcbiClient):
        self._client = client

    def fetch_full_records(self, term: str, db: str) -> List[PubMedArticle] | None:
        """Performs a search and fetches the full records."""
        try:
            search_results = self._client.esearch(db=db, term=term)
            count = int(search_results["Count"])
            webenv = search_results["WebEnv"]
            query_key = search_results["QueryKey"]
            print(f"NCBI Provider: Found {count} results.")

            if count == 0:
                return []

            batch_size = 100
            all_records = []
            for start in range(0, min(count, 1000), batch_size): # Limit to 1000 records
                records_data = self._client.efetch(db=db, webenv=webenv, query_key=query_key, retstart=start, retmax=batch_size)
                all_records.extend(records_data['PubmedArticle'])
                sleep(0.4)
            
            print("NCBI Provider: Finished fetching records.")
            return self._parse_pubmed_records(all_records)

        except Exception as e:
            print(f"NCBI Provider: An error occurred: {e}")
            return None

    def save_records_to_file(self, records: List[PubMedArticle] | None, filename: str):
        """Saves a list of PubMedArticle objects to a specified file (CSV, JSON, or TXT)."""
        if not records:
            print("Provider: No records to save.")
            return

        try:
            article_dicts = [article.model_dump() for article in records]
            df = pd.DataFrame(article_dicts)
            
            # Define a consistent column order for CSV files
            csv_columns = ['PMID', 'Year', 'Journal', 'Title', 'Abstract']

            if filename.endswith('.csv'):
                df.to_csv(filename, index=False, columns=csv_columns)
                print(f"Provider: Successfully saved {len(records)} results to {filename}")
            elif filename.endswith('.json'):
                df.to_json(filename, orient='records', indent=4)
                print(f"Provider: Successfully saved {len(records)} results to {filename}")
            elif filename.endswith('.txt'):
                with open(filename, 'w', encoding='utf-8') as f:
                    for i, article in enumerate(records):
                        f.write(f"Record #{i+1}\n")
                        f.write(f"PMID: {article.PMID}\n")
                        f.write(f"Title: {article.Title}\n")
                        f.write(f"Journal: {article.Journal} ({article.Year})\n")
                        f.write(f"Abstract: {article.Abstract}\n")
                        f.write("\n---\n\n")
                print(f"Provider: Successfully saved {len(records)} results to {filename}")
            else:
                print(f"Provider: Invalid file format for '{filename}'. Please use .csv, .json, or .txt.")

        except Exception as e:
            print(f"Provider: Failed to save file '{filename}'. Error: {e}")

    def _parse_pubmed_records(self, records: list) -> List[PubMedArticle]:
        """Parses the raw XML data from efetch into a list of PubMedArticle models."""
        parsed_articles = []
        for article in records:
            citation = article.get('MedlineCitation', {})
            article_info = citation.get('Article', {})
            
            title = article_info.get('ArticleTitle', 'No Title Found')
            abstract_parts = article_info.get('Abstract', {}).get('AbstractText', [])
            abstract = ' '.join(abstract_parts) if abstract_parts else 'No Abstract Found'
            
            journal_info = article_info.get('Journal', {})
            journal_name = journal_info.get('Title', 'No Journal Found')
            pub_date = journal_info.get('JournalIssue', {}).get('PubDate', {})
            year = pub_date.get('Year', pub_date.get('MedlineDate', 'No Year Found'))
            
            pmid = citation.get('PMID', '')

            parsed_articles.append(PubMedArticle(
                PMID=str(pmid), 
                Title=str(title), 
                Abstract=str(abstract), 
                Journal=str(journal_name), 
                Year=str(year)
            ))
        print(f"NCBI Provider: Successfully parsed {len(parsed_articles)} articles.")
        return parsed_articles

# ==============================================================================
# WEB OF SCIENCE (WOS) PROVIDER
# ==============================================================================
class WosProvider:
    """The high-level provider for Web of Science search workflows."""
    PAGE_LIMIT = 10 
    
    def __init__(self, client: WosStarterClient):
        self._client = client

    def search_and_fetch_all(self, term: str, db: str, sort_field: str) -> List[WosArticle] | None:
        """Performs the complete WOS search and fetch workflow."""
        try:
            initial_results = self._client.search(term=term, page=1, limit=1, db=db, sort_field=sort_field)
            total_hits = initial_results.get('metadata', {}).get('total', 0)
            print(f"WOS Provider: Found {total_hits} total results.")
            
            if total_hits == 0:
                return []
            
            all_results = []
            max_pages = 5 # Hard limit for now to avoid excessive calls
            
            for i in range(1, max_pages + 1):
                if (i - 1) * self.PAGE_LIMIT >= total_hits:
                    break # Stop if we've fetched all available records
                page_results = self._client.search(term=term, page=i, limit=self.PAGE_LIMIT, db=db, sort_field=sort_field)
                page_hits = page_results.get('hits', [])
                if not page_hits:
                    print(f"WOS Provider: No more results on page {i}. Stopping.")
                    break
                
                all_results.extend(page_hits)
                print(f"WOS Provider: Successfully fetched {len(page_hits)} results from page {i}.")
                sleep(0.5)

            print(f"WOS Provider: Finished fetching. Total results: {len(all_results)}.")
            return self._parse_wos_records(all_results)

        except HTTPError as e:
            print(f"WOS Provider: An API error occurred: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            print(f"WOS Provider: An error occurred during fetch: {e}")
            return None

    def search_and_save_all(self, term: str, db: str, sort_field: str, filename: str) -> bool:
        """Searches WoS and saves the results to a file."""
        print(f"WOS Provider: Starting search for '{term}'...")
        articles = self.search_and_fetch_all(term, db, sort_field)
        
        if articles is None:
            print("WOS Provider: Search failed, nothing to save.")
            return False
        if not articles:
            print("WOS Provider: No articles found, nothing to save.")
            return True

        try:
            article_dicts = [article.model_dump() for article in articles]
            df = pd.DataFrame(article_dicts)
            
            # Define a consistent column order for CSV files
            csv_columns = ['UID', 'DOI', 'Year', 'Journal', 'Title', 'Authors']

            if filename.endswith('.csv'):
                df.to_csv(filename, index=False, columns=csv_columns)
                print(f"WOS Provider: Successfully saved {len(articles)} results to {filename}")
            elif filename.endswith('.json'):
                df.to_json(filename, orient='records', indent=4)
                print(f"WOS Provider: Successfully saved {len(articles)} results to {filename}")
            elif filename.endswith('.txt'):
                with open(filename, 'w', encoding='utf-8') as f:
                    for i, article in enumerate(articles):
                        f.write(f"Record #{i+1}\n")
                        f.write(f"UID: {article.UID}\n")
                        f.write(f"DOI: {article.DOI}\n")
                        f.write(f"Title: {article.Title}\n")
                        f.write(f"Authors: {article.Authors}\n")
                        f.write(f"Journal: {article.Journal} ({article.Year})\n")
                        f.write("\n---\n\n")
                print(f"WOS Provider: Successfully saved {len(articles)} results to {filename}")
            else:
                print(f"WOS Provider: Invalid file format for '{filename}'. Please use .csv, .json, or .txt.")
                return False
            return True
        except Exception as e:
            print(f"WOS Provider: Failed to save file '{filename}'. Error: {e}")
            return False

    def _parse_wos_records(self, records: list) -> List[WosArticle]:
        """Parses the raw JSON data from the API into a list of WosArticle models."""
        parsed_articles = []
        for record in records:
            if not isinstance(record, dict): continue # Skip if a record is not a dictionary

            uid = record.get('uid', 'N/A')
            title = record.get('title', 'N/A')

            # Robustly parse identifier info (DOI)
            identifiers_info = record.get('identifiers')
            doi = 'N/A'
            if isinstance(identifiers_info, dict):
                doi = identifiers_info.get('doi', 'N/A')

            # Robustly parse source info (Journal, Year)
            source_info = record.get('source')
            year, journal = ('N/A', 'N/A')
            if isinstance(source_info, dict):
                year = source_info.get('publishYear', 'N/A')
                journal = source_info.get('sourceTitle', 'N/A')

            # Robustly parse author info
            names_info = record.get('names', {})
            authors = 'N/A'
            if isinstance(names_info, dict):
                authors_list = names_info.get('authors', [])
                if authors_list:
                    author_names = []
                    for author in authors_list:
                        if isinstance(author, dict):
                            author_names.append(author.get('displayName', ''))
                        elif isinstance(author, str):
                            author_names.append(author)
                    authors = '; '.join(filter(None, author_names))

            parsed_articles.append(WosArticle(
                UID=str(uid),
                DOI=str(doi),
                Title=str(title),
                Authors=str(authors),
                Journal=str(journal),
                Year=str(year)
            ))
        print(f"WOS Provider: Successfully parsed {len(parsed_articles)} articles.")
        return parsed_articles