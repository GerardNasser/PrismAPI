from pydantic import BaseModel, Field
from typing import Union, List

# A detailed system prompt to guide the LLM's behavior.
# This is crucial for consistency and accuracy.
SYSTEM_PROMPT = """
You are an expert assistant for searching scientific databases, including the National Center
for Biotechnology Information (NCBI) Entrez databases and the Web of Science (WoS). Your goal is
to translate a user's natural language request into a precise and effective call to one of the
available tools.

Key principles to follow:
1.  **Database Choice**: Determine if the user wants to search NCBI (e.g., 'pubmed', 'protein', 'gene')
    or Web of Science. If they don't specify, ask for clarification unless the query strongly implies one
    (e.g., "find articles" often implies PubMed or WoS).
2.  **Preserve Exact Queries**: If a user provides a search term in quotation marks
    (e.g., "human cancer cells"), you MUST use that exact term in the `term` parameter.
    Do not modify or rephrase it.
3.  **Use Your Judgment**: For unquoted, more general queries (e.g., "papers about cancer"),
    you can refine the search term to be more effective if necessary.
4.  **Be Specific**: Always provide clear, specific arguments for the tool calls. Do not
    leave mandatory fields blank.
5.  **Choose the Right Tool for the Database**:
    - For NCBI, use tools like `GetSummary`, `FetchFullRecords`, and `FindRelated`.
    - For Web of Science, use `SearchWos` or `SearchWosAndSave`.
"""

# --- NCBI Tools ---

class GetSummary(BaseModel):
    """
    Use this action to get brief summaries of records from any NCBI Entrez database.
    This is faster and more efficient than fetching full records.
    """
    db: str = Field(description="The NCBI database to search (e.g., 'pubmed', 'protein', 'gene').")
    term: str = Field(description="The user's specific search query. For example, 'BRCA1 and human cancer'.")

class FetchFullRecords(BaseModel):
    """
    Use this action to retrieve complete records from an NCBI Entrez database. This is slower
    but provides all available data, such as article abstracts from PubMed.
    """
    db: str = Field(description="The NCBI database to search (e.g., 'pubmed', 'protein').")
    term: str = Field(description="The user's search query.")

class FetchAndSave(BaseModel):
    """
    Use this action when the user wants to search an NCBI database and save the full results to a file.
    """
    db: str = Field(description="The NCBI database to search.")
    term: str = Field(description="The user's search query.")
    filename: str = Field(description="The name of the file to save results to. Use a .csv or .json extension (e.g., 'crispr_results.csv', 'proteins.json').")

class FindRelated(BaseModel):
    """
    Use this action to find related data by linking two NCBI Entrez databases.
    """
    source_db: str = Field(description="The NCBI database you are starting from (e.g., 'pubmed').")
    source_term: str = Field(description="The search term to find the initial set of records in the source_db.")
    target_db: str = Field(description="The target NCBI database to find related records in (e.g., 'nuccore').")

class RawNcbiSearch(BaseModel):
    """
    **EXPERT USE ONLY**. Use this when the user provides a complex, pre-formatted query string with boolean operators, or a query enclosed in backticks (`). This tool bypasses AI interpretation.
    """
    term: str = Field(description="The raw, exact search string to be sent to the NCBI API.")
    db: str = Field(default="pubmed", description="The NCBI database to search.")
    
# --- Web of Science Tools ---

class SearchWos(BaseModel):
    """
    Use this action to search the Web of Science database and display the results.
    """
    term: str = Field(description="The user's specific search query for Web of Science.")

class SearchWosAndSave(BaseModel):
    """
    Use this action when the user wants to search Web of Science and save the results to a CSV or JSON file.
    """
    term: str = Field(description="The user's search query for Web of Science.")
    filename: str = Field(description="The name of the file to save results to. Must end in .csv or .json.")


Action = Union[GetSummary, FetchFullRecords, FetchAndSave, FindRelated, SearchWos, SearchWosAndSave]