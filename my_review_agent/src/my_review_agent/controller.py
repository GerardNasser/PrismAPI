import google.generativeai as genai
from .provider import NcbiProvider, WosProvider
from .actions import (
    Action, GetSummary, FetchFullRecords, FetchAndSave, FindRelated, RawNcbiSearch,
    SearchWos, SearchWosAndSave, SYSTEM_PROMPT
)

class Controller:
    """The AI brain that uses the Gemini API to orchestrate searches."""

    def __init__(self, ncbi_provider: NcbiProvider, wos_provider: WosProvider):
        self._ncbi_provider = ncbi_provider
        self._wos_provider = wos_provider
        self._llm_client = genai.GenerativeModel("gemini-1.5-flash-latest")
        
        self._tools = [GetSummary, FetchFullRecords, FetchAndSave, FindRelated, RawNcbiSearch, SearchWos, SearchWosAndSave]
        
        self._chat = self._llm_client.start_chat(enable_automatic_function_calling=False)
        self._chat.send_message(f"SYSTEM INSTRUCTIONS: {SYSTEM_PROMPT}")

    def process_command(self, user_prompt: str):
        print(f"\n[Controller] User command received: '{user_prompt}'")
        try:
            response = self._chat.send_message(user_prompt, tools=self._tools)
            function_call = response.candidates[0].content.parts[0].function_call
            
            if not function_call or not function_call.name:
                print("[Controller] LLM did not choose a tool. Responding with text:")
                print(response.text)
                return

            action_name = function_call.name
            args = dict(function_call.args)
            print(f"[Controller] LLM chose to call '{action_name}' with args: {args}")

            # --- NCBI Actions ---
            if action_name == "GetSummary":
                results = self._ncbi_provider.get_summaries(db=args['db'], term=args['term'])
                if results:
                    print(f"\n--- Top 5 NCBI Summaries for '{args['term']}' in '{args['db']}' ---")
                    for item in results[:5]: print(f"- UID: {item.get('Id', 'N/A')}, Title: {item.get('Title', 'N/A')}")
                elif results == []: print(f"No results found for '{args['term']}'.")

            elif action_name == "FetchFullRecords":
                results = self._ncbi_provider.fetch_full_records(db=args['db'], term=args['term'])
                if results and args['db'] == 'pubmed':
                    print(f"\n--- Top 3 NCBI Full Records for '{args['term']}' ---")
                    for article in results[:3]: print(f"\nTitle: {article.Title}\nJournal: {article.Journal} ({article.Year})\nPMID: {article.PMID}\nAbstract: {article.Abstract[:200]}...")
                elif results:
                    print(f"\n--- Fetched {len(results)} raw records. ---")
                    print(results[0])
                elif results == []: print(f"No results found for '{args['term']}'.")
            
            elif action_name == "RawNcbiSearch":
                print(f"[Controller] Bypassing LLM interpretation for raw search.")
                results = self._ncbi_provider.fetch_full_records(db=args['db'], term=args['term'])
                if results and args['db'] == 'pubmed':
                    print(f"\n--- Top 3 NCBI Full Records for Raw Search ---")
                    for article in results[:3]: print(f"\nTitle: {article.Title}\nJournal: {article.Journal} ({article.Year})\nPMID: {article.PMID}")
                elif results:
                    print(f"\n--- Fetched {len(results)} raw records. ---")
                elif results == []: print(f"No results found for raw query.")


            elif action_name == "FetchAndSave":
                print(f"Starting NCBI operation to save results to '{args['filename']}'...")
                full_records = self._ncbi_provider.fetch_full_records(term=args['term'], db=args.get('db', 'pubmed'))
                if full_records is not None:
                    success = self._ncbi_provider.save_results_to_file(data=full_records, filename=args['filename'])
                    print("Save operation completed.")
                else: print(f"Could not fetch records, aborting save operation.")

            elif action_name == "FindRelated":
                links = self._ncbi_provider.find_and_link(source_db=args['source_db'], source_term=args['source_term'], target_db=args['target_db'])
                if links:
                    print(f"\n--- Top 5 NCBI Links from '{args['source_db']}' to '{args['target_db']}' ---")
                    for link in links[:5]: print(f"- Source ID {link['SourceID']} -> Target ID {link['TargetID']}")
                elif links == []: print(f"No links found.")

            # --- Web of Science Actions ---
            elif action_name == "SearchWos":
                results = self._wos_provider.search_and_fetch(term=args['term'])
                if results:
                    print(f"\n--- Top 5 Web of Science Results for '{args['term']}' ---")
                    for article in results[:5]:
                        print(f"\nTitle: {article.Title}\nJournal: {article.Journal} ({article.Year})\nDOI: {article.DOI}")
                elif results == []: print(f"No results found for '{args['term']}'.")

            elif action_name == "SearchWosAndSave":
                print(f"Starting Web of Science operation to save results to '{args['filename']}'...")
                records = self._wos_provider.search_and_fetch(term=args['term'])
                if records is not None:
                    success = self._wos_provider.save_results_to_file(data=records, filename=args['filename'])
                    print("Save operation completed.")
                else: print(f"Could not fetch records, aborting save operation.")

            else:
                print(f"Error: LLM chose an unknown function '{action_name}'")
        except Exception as e:
            print(f"[Controller] An error occurred: {e}")