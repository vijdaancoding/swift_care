import os
import google.generativeai as genai
from dotenv import load_dotenv

from utils.global_history import get_shared_chat, history_manager

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")

genai.configure(api_key=api_key)

def create_agent(prompt: str, agent_name: str = "unknown"):
    """
    Create an agent with shared conversation history
    
    Args:
        prompt (str): System instruction for the agent
        agent_name (str): Name of the agent for history tracking
    
    Returns:
        chat: Gemini chat instance with shared history
    """
    # Get shared chat instance that maintains history across agents
    chat = get_shared_chat(prompt, agent_name)
    
    print(f"Created/Retrieved {agent_name} agent with shared history")
    stats = history_manager.get_stats()
    print(f"Session stats: {stats['total_messages']} messages, {stats['agent_transitions']} transitions")
    
    return chat

def create_fresh_agent(prompt: str):
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=prompt  # system prompt goes here
    )

    chat = model.start_chat()
    return chat