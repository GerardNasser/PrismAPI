import google.generativeai as genai
from google.generativeai.types import Tool, FunctionDeclaration
from .provider import GalaxyProvider

class Controller:
    def __init__(self, provider: GalaxyProvider):
        self._provider = provider
        self._llm_client = genai.GenerativeModel("gemini-1.5-flash")
        
        # This "menu" of tools is what the LLM reads to make a choice.
        # The descriptions have been improved for better accuracy.
        self._tools = Tool(
            function_declarations=[
                FunctionDeclaration(
                    name="fetch_all_libraries",
                    description="Use this to list all DATA LIBRARIES. Data libraries are used for storing and sharing datasets.",
                ),
                FunctionDeclaration(
                    name="fetch_all_histories_with_details",
                    description="Use this to list all user HISTORIES. Histories are records of past analyses and computations.",
                ),
                FunctionDeclaration(
                    name="fetch_all_workflows",
                    description="Use this to list all WORKFLOWS. Workflows are reusable, multi-step analysis pipelines.",
                ),
                FunctionDeclaration(
                    name="fetch_all_tools",
                    description="Use this to list all available TOOLS. A tool is a single software program for a specific task.",
                ),
            ]
        )

    def process_command(self, user_prompt: str):
        print(f"\n[Controller] User command received: '{user_prompt}'")
        try:
            # 1. Send the prompt and the "menu" of tools to the Gemini API
            response = self._llm_client.generate_content(
                user_prompt,
                tools=[self._tools],
            )
            
            # 2. Check if the LLM chose a tool to call
            response_part = response.candidates[0].content.parts[0]
            if not response_part.function_call or not response_part.function_call.name:
                print("[Controller] LLM did not choose a tool. Responding with text:")
                print(response.text)
                return

            # 3. Get the name of the function the LLM chose
            function_name = response_part.function_call.name
            print(f"[Controller] LLM chose to call provider function: '{function_name}'")

            # 4. Find and call the corresponding method in our provider
            provider_method = getattr(self._provider, function_name, None)
            
            if provider_method and callable(provider_method):
                results = provider_method()
                # 5. Print the results if any were returned
                if results:
                    for item in results:
                        print(item.model_dump_json(indent=2))
                else:
                    print(f"[Controller] Function '{function_name}' did not return any results.")
            else:
                print(f"Error: LLM chose an unknown function '{function_name}'")

        except Exception as e:
            print(f"[Controller] An error occurred: {e}")