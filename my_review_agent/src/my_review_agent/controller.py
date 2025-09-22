import google.generativeai as genai
from .provider import NcbiProvider, WosProvider
from .actions import SYSTEM_PROMPT, ALL_ACTIONS

class Controller:
    """The AI brain that uses the Gemini API to orchestrate searches."""

    def __init__(self, ncbi_provider: NcbiProvider, wos_provider: WosProvider, default_ncbi_db: str, default_wos_db: str, default_wos_sort: str):
        self._ncbi_provider = ncbi_provider
        self._wos_provider = wos_provider
        self._llm_client = genai.GenerativeModel("gemini-1.5-flash", system_instruction=SYSTEM_PROMPT)
        self._chat = self._llm_client.start_chat(history=[])
        self._tools = ALL_ACTIONS

        # Store the user-configured defaults from the .env file
        self._default_ncbi_db = default_ncbi_db
        self._default_wos_db = default_wos_db
        self._default_wos_sort = default_wos_sort

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
            args = function_call.args
            print(f"[Controller] LLM chose to call '{action_name}' with args: {dict(args)}")

            # --- Handle the different actions based on the LLM's choice ---
            
            if action_name == "SearchNcbi":
                ncbi_db = args.get('db', self._default_ncbi_db)
                results = self._ncbi_provider.fetch_full_records(term=args['term'], db=ncbi_db)
                if results:
                    print(f"\n--- Top 3 Search Results for '{args['term']}' in '{ncbi_db}' ---")
                    for article in results[:3]:
                        print(f"\nTitle: {article.Title}\nJournal: {article.Journal} ({article.Year})\nPMID: {article.PMID}")
                elif results == []:
                    print(f"No results found for '{args['term']}'.")

            elif action_name == "SaveNcbiResults":
                ncbi_db = args.get('db', self._default_ncbi_db)
                records = self._ncbi_provider.fetch_full_records(term=args['term'], db=ncbi_db)
                self._ncbi_provider.save_records_to_file(records, args['filename'])

            elif action_name == "RawNcbiSearch":
                ncbi_db = args.get('db', self._default_ncbi_db)
                results = self._ncbi_provider.fetch_full_records(term=args['term'], db=ncbi_db)
                if results:
                    print(f"\n--- Top 3 Raw Search Results in '{ncbi_db}' ---")
                    for article in results[:3]:
                        print(f"\nTitle: {article.Title}\nJournal: {article.Journal} ({article.Year})\nPMID: {article.PMID}")
                elif results == []:
                    print(f"No results found.")

            elif action_name == "SearchWos":
                wos_db = args.get('db', self._default_wos_db)
                sort_field = self._default_wos_sort # WOS sort field is complex, always use default for now
                
                results = self._wos_provider.search_and_fetch_all(term=args['term'], db=wos_db, sort_field=sort_field)
                if results:
                    print(f"\n--- Top 3 WoS Results for '{args['term']}' in '{wos_db}' ---")
                    for article in results[:3]:
                        print(f"\nTitle: {article.Title}\nJournal: {article.Journal} ({article.Year})\nUID: {article.UID}")
                elif results == []:
                    print(f"No results found for '{args['term']}'.")

            elif action_name == "SearchWosAndSave":
                wos_db = args.get('db', self._default_wos_db)
                sort_field = self._default_wos_sort
                self._wos_provider.search_and_save_all(
                    term=args['term'],
                    db=wos_db,
                    sort_field=sort_field,
                    filename=args['filename']
                )
            
            else:
                print(f"Error: LLM chose an unknown function '{action_name}'")

        except Exception as e:
            print(f"[Controller] An error occurred: {e}")

