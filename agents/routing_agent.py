import os
import google.generativeai as genai
from dotenv import load_dotenv

from mesh.main_simulation import mesh_bridge
from prompts.routing_prompt import SYSTEM_PROMPT

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)


def create_agent():
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=SYSTEM_PROMPT
    )
    return model.start_chat(history=[])

def run_routing_agent():
    chat = create_agent()
    print("👮 Emergency Routing Agent is active.")
    print("------------------------------------------------\n")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["quit", "exit"]:
            print("Agent: Ending conversation. Stay safe.")
            break
        
        user_json = {
            "data" : user_input 
        }

        response = mesh_bridge(user_json, chat.send_message)

        print(response)

        print("Agent:", response['data'])

        if "Routing you to the" in response['data']:
            print("\n✅ Agent has finished routing. Conversation ended.")
            break

if __name__ == "__main__":
    run_routing_agent()
