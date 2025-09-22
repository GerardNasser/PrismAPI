import os
from dotenv import load_dotenv
import google.generativeai as genai

from .client import NcbiClient, WosStarterClient
from .provider import NcbiProvider, WosProvider
from .controller import Controller

def run():
    """Loads environment variables, sets up clients and providers, and runs the main interactive loop."""
    load_dotenv()
    
    # --- Load API Keys and required variables ---
    google_key = os.environ.get("GOOGLE_API_KEY")
    ncbi_email = os.environ.get("NCBI_EMAIL")
    ncbi_api_key = os.environ.get("NCBI_API_KEY") # Optional but recommended
    wos_api_key = os.environ.get("WOS_API_KEY")
    wos_base_url = os.environ.get("WOS_BASE_URL")

    if not all([google_key, ncbi_email, wos_api_key, wos_base_url]):
        print("Error: GOOGLE_API_KEY, NCBI_EMAIL, WOS_API_KEY, and WOS_BASE_URL must be set in your .env file.")
        return

    genai.configure(api_key=google_key)

    # --- Load new defaults from .env ---
    default_ncbi_db = os.environ.get("DATABASE", "pubmed")
    default_wos_db = os.environ.get("DATABASE_CODE", "WOS")
    
    # Logic to build the WOS sort field string from .env variables
    wos_sort_field = os.environ.get("SORT_FIELD", "LD")
    wos_ascending = os.environ.get("ASCENDING", "true").lower()
    sort_direction = "A" if wos_ascending == 'true' else "D"
    default_wos_sort = f"{wos_sort_field} {sort_direction}"

    # --- Setup Phase ---
    ncbi_client = NcbiClient(email=ncbi_email, api_key=ncbi_api_key)
    wos_client = WosStarterClient(api_key=wos_api_key, base_url=wos_base_url)
    
    ncbi_provider = NcbiProvider(client=ncbi_client)
    wos_provider = WosProvider(client=wos_client)
    
    # Pass defaults into the controller on initialization
    controller = Controller(
        ncbi_provider=ncbi_provider, 
        wos_provider=wos_provider,
        default_ncbi_db=default_ncbi_db,
        default_wos_db=default_wos_db,
        default_wos_sort=default_wos_sort
    )
    
    print("Multi-Database Agent (Gemini Edition) is ready. Type 'exit' to quit.")
    print("\n--- Example Prompts")
    print("1. NCBI Search: 'Find me papers about CRISPR in the protein database'")
    print("2. WoS Search: 'Search web of science for articles on urban gradients'")
    print("3. Save to File: 'Search pubmed for immunology and save to results.csv'")
    print("4. Raw Search (NCBI): 'Search pubmed for `(asthma[MeSH Terms]) AND (review[Publication Type])`'")
    print("5. Follow-up (Memory): First search for something, then ask a follow-up like 'of those, which were published in 2023?'\n")

    # --- Execution Phase (Interactive Loop) ---
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break
            if not user_input:
                continue
            controller.process_command(user_input)
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

if __name__ == "__main__":
    run()

