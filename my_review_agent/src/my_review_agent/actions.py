from pydantic import BaseModel, Field
from typing import Union, List

# ==============================================================================
# SYSTEM PROMPT
# ==============================================================================
SYSTEM_PROMPT = """
You are a specialized AI agent designed to interact with the NCBI and Web of Science (WoS) APIs. 
Your primary function is to help users conduct scientific literature reviews.

You have access to a specific set of tools to perform searches and save data. 
Your main responsibilities are:
1.  **Interpret User Queries**: Understand the user's request and determine the most appropriate tool to use.
2.  **Formulate Search Terms**: Extract the core search query from the user's prompt.
3.  **Preserve Exact Queries**: If a user provides a search term in quotes ("...") or backticks (`...`), you MUST use that exact term without any modifications or rephrasing. For complex boolean queries, this is critical.
4.  **Tool Selection**: Based on the user's intent (e.g., search vs. save, NCBI vs. WoS), select the correct tool and provide the necessary arguments.
5.  **Database Specificity**: Pay close attention to which database (e.g., pubmed, wos) the user wants to search.

Do not answer general knowledge questions. Only use the provided tools to fulfill the user's request.
"""

# ==============================================================================
# NCBI ACTIONS
# ==============================================================================
class SearchNcbi(BaseModel):
    """
    Use this action to search an NCBI database and DISPLAY a summary of the results on the screen. This is for VIEWING results only. DO NOT use this tool if the user mentions 'save', 'export', or a filename.
    """
    term: str = Field(description="The user's specific search query. For example, 'BRCA1 and human cancer'.")
    db: str = Field(description="The NCBI database to search (e.g., 'pubmed', 'protein'). Defaults to the user's configured default if not specified.")

class SaveNcbiResults(BaseModel):
    """
    Use this action ONLY if the user's prompt contains explicit trigger words like 'save', 'export', 'download', or includes a filename. For simple searches to view on screen, use the SearchNcbi tool.
    """
    term: str = Field(description="The user's search query.")
    db: str = Field(description="The NCBI database to search.")
    filename: str = Field(description="The name of the file to save results to. If the user does not specify a file extension, default to '.csv'.")

class RawNcbiSearch(BaseModel):
    """
    Use this specialized action ONLY for very long, complex, or pre-formatted NCBI search strings, especially those in backticks (`...`). It bypasses AI query modification.
    """
    term: str = Field(description="The exact, complex search string provided by the user.")
    db: str = Field(description="The NCBI database to search.")

# ==============================================================================
# WEB OF SCIENCE ACTIONS
# ==============================================================================
class SearchWos(BaseModel):
    """
    Use this action to search Web of Science and DISPLAY a summary of the results on the screen. This does NOT save to a file. DO NOT use this tool if the user mentions 'save', 'export', or a filename.
    """
    term: str = Field(description="The user's search query for Web of Science.")

class SearchWosAndSave(BaseModel):
    """
    Use this action ONLY if the user's prompt contains explicit trigger words like 'save', 'export', 'download', or includes a filename. For simple searches to view on screen, use the SearchWos tool.
    """
    term: str = Field(description="The user's search query.")
    filename: str = Field(description="The name of the file to save results to. If the user does not specify a file extension, default to '.csv'.")

# ==============================================================================
# AGGREGATED ACTIONS
# ==============================================================================
ALL_ACTIONS = [SearchNcbi, SaveNcbiResults, RawNcbiSearch, SearchWos, SearchWosAndSave]

