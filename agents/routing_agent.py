import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

SYSTEM_PROMPT = """
You are an emergency routing agent. Your role is:
- Greet the user politely and ask what their emergency is.
- If the user gives a greeting or unrelated response, redirect them back kindly.
- Collect enough context before deciding whether the issue is:
  1. Crime (violence, theft, assault, suspicious activity, etc.)
  2. Disaster (fire, flood, earthquake, accident, etc.)
  3. Medical (injury, illness, unconsciousness, etc.)
- IMPORTANT: Do not classify or route based on single vague words like "help", "dying", "emergency".
- You MUST ask at least two clarifying questions (e.g., what happened, where, who is involved, what symptoms, what caused it) before routing.
- Only once you have enough detail, respond exactly with:
  "Routing you to the [CATEGORY] emergency response team now."
- Until then, keep the conversation natural, empathetic, and professional.
"""

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

        response = chat.send_message(user_input)
        print("Agent:", response.text)

        if "Routing you to the" in response.text:
            print("\n✅ Agent has finished routing. Conversation ended.")
            break

if __name__ == "__main__":
    run_routing_agent()
