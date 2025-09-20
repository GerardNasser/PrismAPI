import os
from dotenv import load_dotenv
import google.generativeai as genai
from .client import NcbiClient, WosClient
from .provider import NcbiProvider, WosProvider
from .controller import Controller

def run():
    """
    Initializes and runs the interactive multi-database agent.
    """
    load_dotenv()
    google_key = os.environ.get("GOOGLE_API_KEY")
    ncbi_email = os.environ.get("NCBI_EMAIL")
    wos_api_key = os.environ.get("WOS_API_KEY")
    ncbi_api_key = os.environ.get("NCBI_API_KEY") # Optional but recommended

    if not all([google_key, ncbi_email, wos_api_key]):
        print("Error: GOOGLE_API_KEY, NCBI_EMAIL, and WOS_API_KEY must be set in your .env file.")
        return

    genai.configure(api_key=google_key)

    try:
        # Setup Phase for NCBI
        ncbi_client = NcbiClient(email=ncbi_email, api_key=ncbi_api_key)
        ncbi_provider = NcbiProvider(client=ncbi_client)

        # Setup Phase for Web of Science
        wos_client = WosClient(api_key=wos_api_key)
        wos_provider = WosProvider(client=wos_client)

        # The controller gets all providers
        controller = Controller(ncbi_provider=ncbi_provider, wos_provider=wos_provider)
    except Exception as e:
        print(f"Failed to initialize the agent. Error: {e}")
        return
    
    print("--- Multi-Database Research Agent (Gemini Edition) ---")
    print("The agent is ready. Type 'exit' or 'quit' to end.")
    print("\n--- Example Prompts ---")
    print("1. NCBI Search: 'Fetch full articles from pubmed for \"crispr cas9 therapy\"'")
    print("2. Web of Science Search: 'Search web of science for \"carbon nanotube composites\"'")
    print("3. Save from WoS: 'Find articles in web of science about \"machine learning in chemistry\" and save to wos_results.json'")
    print("4. Save from NCBI: 'Search for gene database records on human BRCA1 and save to ncbi_genes.csv'\n")

    # Execution Phase (Interactive Loop)
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break
            if not user_input.strip():
                continue
            controller.process_command(user_input)
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nAn unexpected error occurred in the main loop: {e}")

