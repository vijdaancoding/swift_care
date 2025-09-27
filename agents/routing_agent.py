from utils.agent_creation import create_agent
from utils.global_history import history_manager, add_agent_transition
from mesh.main_simulation import mesh_bridge


def run_routing_agent(prompt: str):

    agent_name = "routing"

    chat = create_agent(prompt, agent_name)
    print("Emergency Routing Agent is active.")
    print("------------------------------------------------\n")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["quit", "exit"]:
            print("Agent: Ending conversation. Stay safe.")
            break
        elif user_input.lower() == "history":
            history_manager.print_history_debug()
            continue
        
        user_json = {
            "data" : user_input 
        }

        response = mesh_bridge(user_json, chat.send_message, agent_name)
        print("Routing Agent:", response['data'])

        print(f"Chat History Length: {len(chat.history)}")

        if "ROUTE:" in response['data']:
            category = response['data'].split("ROUTE:")[-1].strip()
            print(f"\nRouting complete. Handing off to {category} agent...\n")

            add_agent_transition(agent_name, category.lower(), "Routing Decision")

            return category
        
    return None
