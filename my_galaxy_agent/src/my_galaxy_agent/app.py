import os
from dotenv import load_dotenv
import google.generativeai as genai
from .client import GalaxyApiClient
from .provider import GalaxyProvider
from .controller import Controller

def run():
    load_dotenv()
    google_key = os.environ.get("GOOGLE_API_KEY")
    galaxy_url = os.environ.get("GALAXY_URL")
    galaxy_key = os.environ.get("GALAXY_API_KEY")

    if not all([google_key, galaxy_url, galaxy_key]):
        print("Error: GOOGLE_API_KEY, GALAXY_URL, and GALAXY_API_KEY must be set.")
        return

    # Configure the Gemini library with your API key
    genai.configure(api_key=google_key)

    # --- Setup Phase ---
    galaxy_client = GalaxyApiClient(base_url=galaxy_url, api_key=galaxy_key)
    provider = GalaxyProvider(client=galaxy_client)
    controller = Controller(provider=provider)
    
    print("Gemini Galaxy Agent is ready. Type 'exit' or 'quit' to end the session.")

    # --- Execution Phase (Interactive Loop) ---
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break
            if not user_input:
                continue
            # Pass the user's command to the controller
            controller.process_command(user_input)
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

if __name__ == "__main__":
    run()