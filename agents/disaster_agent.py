from utils.agent_creation import create_agent
from mesh.main_simulation import mesh_bridge
from utils.global_history import history_manager, add_agent_transition

def run_disaster_agent(prompt: str):

    agent_name = "disaster"
    
    if history_manager.conversation_history:
        recent_context = history_manager.get_history_summary(5)
        enhanced_prompt = f"""{prompt}

IMPORTANT: You are now the DISASTER AGENT. 
Your role is to calmly gather details about disasters or emergencies such as fires, earthquakes, floods, accidents, or building collapses, 
and provide supportive guidance until help can be arranged.

You have the following conversation context from the routing agent:

CONVERSATION CONTEXT:
{recent_context}

Continue the conversation as the disaster agent, referencing this context as needed to provide appropriate disaster emergency assistance."""
    else:
        enhanced_prompt = prompt

    chat = create_agent(enhanced_prompt, agent_name)

    print("🌍 Emergency Disaster Agent is active.")
    print(f"💬 Current session has {len(history_manager.conversation_history)} messages")
    print("------------------------------------------------\n")
    
    if history_manager.conversation_history:
        print("📋 Recent conversation context:")
        recent_summary = history_manager.get_history_summary(3)
        for line in recent_summary.split('\n')[-3:]:  # Last 3 messages
            print(f"   {line}")
        print()

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["quit", "exit"]:
            print("Agent: Stay safe. Disaster reporting session ended.")
            break
        elif user_input.lower() == "route":
            print("Agent: Returning to routing agent...")
            add_agent_transition(agent_name, "routing", "User requested return to routing")
            return "routing"
        elif user_input.lower() == "history":
            # Show full conversation history
            history_manager.print_history_debug(10)
            continue
        elif user_input.lower() == "summary":
            # Generate disaster summary
            summary_prompt = "Based on our conversation, provide a brief disaster incident report of the key details gathered."
            summary_json = {"data": summary_prompt}
            summary_response = mesh_bridge(summary_json, chat.send_message, agent_name)
            print(f"\n📋 Disaster Report Summary:\n{summary_response['data']}\n")
            continue
        
        user_json = {
            "data": user_input 
        }

        response = mesh_bridge(user_json, chat.send_message, agent_name)
        print("Disaster Agent:", response['data'])

        print(f"🔍 Shared chat history length: {len(chat.history)}")

        if isinstance(response, dict) and "summary" in response:
            summary = response["summary"]

            print("\nAgent: Thank you. Emergency services are being notified immediately.")
            print("✅ Disaster report complete. Returning summary.\n")

            return summary
    
    return None

