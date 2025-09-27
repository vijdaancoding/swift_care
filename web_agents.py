"""
Web-compatible agent functions that don't use terminal input
"""

from utils.agent_creation import create_agent
from utils.global_history import history_manager, add_agent_transition
from mesh.main_simulation import mesh_bridge
import re
import json

def run_routing_agent_web(prompt: str, user_input: str):
    """Web-compatible routing agent that processes a single input"""
    agent_name = "routing"
    chat = create_agent(prompt, agent_name)
    print("👮 Emergency Routing Agent is active.")
    print("------------------------------------------------")
    
    # Process the user input directly
    user_json = {"data": user_input}
    response = mesh_bridge(user_json, chat.send_message, agent_name)
    print("Routing Agent:", response['data'])
    print(f"Chat History Length: {len(chat.history)}")

    # Check for explicit routing decision
    if "ROUTE:" in response['data']:
        category = response['data'].split("ROUTE:")[-1].strip()
        print(f"\n✅ Routing complete. Handing off to {category} agent...")
        add_agent_transition(agent_name, category.lower(), "Routing Decision")
        return category
    
    # If no explicit routing decision, try to determine from content
    user_lower = user_input.lower()
    if any(word in user_lower for word in ['medical', 'doctor', 'hospital', 'pain', 'injury', 'sick', 'medicine', 'chest', 'heart', 'breathing', 'help']):
        print(f"\n✅ Routing complete. Handing off to Medical agent...")
        add_agent_transition(agent_name, "medical", "Routing Decision")
        return "medical"
    elif any(word in user_lower for word in ['crime', 'theft', 'robbery', 'assault', 'police', 'stolen', 'burglary', 'suspicious']):
        print(f"\n✅ Routing complete. Handing off to Crime agent...")
        add_agent_transition(agent_name, "crime", "Routing Decision")
        return "crime"
    elif any(word in user_lower for word in ['fire', 'disaster', 'flood', 'earthquake', 'emergency', 'explosion', 'accident']):
        print(f"\n✅ Routing complete. Handing off to Disaster agent...")
        add_agent_transition(agent_name, "disaster", "Routing Decision")
        return "disaster"
    
    # Default to medical for general help requests
    print(f"\n✅ Routing complete. Handing off to Medical agent...")
    add_agent_transition(agent_name, "medical", "Routing Decision")
    return "medical"

def run_medical_agent_web(prompt: str, user_input: str):
    """Web-compatible medical agent that processes a single input"""
    agent_name = "medical"
    
    # Enhanced prompt with context if available
    if history_manager.conversation_history:
        recent_context = history_manager.get_history_summary(5)
        enhanced_prompt = f"""{prompt}

IMPORTANT: You are now the MEDICAL AGENT. 
Your role is to assess medical emergencies, provide immediate guidance, and coordinate medical response. 
You have the following conversation context from the routing agent:

CONVERSATION CONTEXT:
{recent_context}

Continue the conversation as the medical agent, referencing this context as needed to provide appropriate medical emergency assistance."""
    else:
        enhanced_prompt = prompt

    chat = create_agent(enhanced_prompt, agent_name)
    print("🏥 Emergency Medical Agent is active.")
    print(f"💬 Current session has {len(history_manager.conversation_history)} messages")
    print("------------------------------------------------")

    # Process the user input directly
    user_json = {"data": user_input}
    response = mesh_bridge(user_json, chat.send_message, agent_name)
    print("Medical Agent:", response['data'])
    print(f"🔍 Shared chat history length: {len(chat.history)}")

    # Try to parse JSON response from AI (same logic as original agent)
    agent_result = None
    
    # 1. Check if the response data is already a dictionary
    if isinstance(response['data'], dict):
        agent_result = response['data']
    
    # 2. If it's a string, try to parse it
    elif isinstance(response['data'], str):
        parsed_json = None
        # Try to find and parse a markdown JSON block
        match = re.search(r"```json\s*(\{.*?\})\s*```", response['data'], re.DOTALL)
        if match:
            try:
                parsed_json = json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        
        # If no markdown block was found, try parsing the entire response string as JSON
        if parsed_json is None:
            try:
                parsed_json = json.loads(response['data'])
            except json.JSONDecodeError:
                pass
        
        agent_result = parsed_json

    # 3. Check if we have a valid dictionary containing the specific keys
    if isinstance(agent_result, dict) and 'incident_type' in agent_result and 'summary' in agent_result:
        print("\nAgent: Please stay calm. Medical help is being arranged right now.")
        print("✅ Medical triage complete. Returning summary.")
        print(agent_result)
        return agent_result
    
    # If no valid JSON structure, generate a fallback incident summary
    incident_summary = {
        "incident_type": "Medical",
        "summary": f"Medical emergency reported: {user_input}. Agent response: {response['data']}",
        "location": "Location not specified",
        "severity": "medium",
        "priority": "HIGH"
    }
    
    print("\nAgent: Please stay calm. Medical help is being arranged right now.")
    print("✅ Medical triage complete. Returning fallback summary.")
    print(incident_summary)
    return incident_summary

def run_crime_agent_web(prompt: str, user_input: str):
    """Web-compatible crime agent that processes a single input"""
    agent_name = "crime"
    
    # Enhanced prompt with context if available
    if history_manager.conversation_history:
        recent_context = history_manager.get_history_summary(5)
        enhanced_prompt = f"""{prompt}

IMPORTANT: You are now the CRIME AGENT. 
Your role is to calmly gather details about crimes and provide supportive guidance until help can be arranged. 
You have the following conversation context from the routing agent:

CONVERSATION CONTEXT:
{recent_context}

Continue the conversation as the crime agent, referencing this context as needed to provide appropriate criminal emergency assistance."""
    else:
        enhanced_prompt = prompt

    chat = create_agent(enhanced_prompt, agent_name)
    print("👮 Emergency Crime Agent is active.")
    print(f"💬 Current session has {len(history_manager.conversation_history)} messages")
    print("------------------------------------------------")

    # Process the user input directly
    user_json = {"data": user_input}
    response = mesh_bridge(user_json, chat.send_message, agent_name)
    print("Crime Agent:", response['data'])
    print(f"🔍 Shared chat history length: {len(chat.history)}")

    # Try to parse JSON response from AI (same logic as original agent)
    agent_result = None
    
    # 1. Check if the response data is already a dictionary
    if isinstance(response['data'], dict):
        agent_result = response['data']
    
    # 2. If it's a string, try to parse it
    elif isinstance(response['data'], str):
        parsed_json = None
        # Try to find and parse a markdown JSON block
        match = re.search(r"```json\s*(\{.*?\})\s*```", response['data'], re.DOTALL)
        if match:
            try:
                parsed_json = json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        
        # If no markdown block was found, try parsing the entire response string as JSON
        if parsed_json is None:
            try:
                parsed_json = json.loads(response['data'])
            except json.JSONDecodeError:
                pass
        
        agent_result = parsed_json

    # 3. Check if we have a valid dictionary containing the specific keys
    if isinstance(agent_result, dict) and 'incident_type' in agent_result and 'summary' in agent_result:
        print("\nAgent: Please stay safe. Police assistance is being arranged right now.")
        print("✅ Crime report complete. Returning summary.")
        print(agent_result)
        return agent_result
    
    # If no valid JSON structure, generate a fallback incident summary
    incident_summary = {
        "incident_type": "Crime",
        "summary": f"Crime incident reported: {user_input}. Agent response: {response['data']}",
        "location": "Location not specified",
        "severity": "medium",
        "priority": "HIGH"
    }
    
    print("\nAgent: Please stay safe. Police assistance is being arranged right now.")
    print("✅ Crime report complete. Returning fallback summary.")
    print(incident_summary)
    return incident_summary

def run_disaster_agent_web(prompt: str, user_input: str):
    """Web-compatible disaster agent that processes a single input"""
    agent_name = "disaster"
    
    # Enhanced prompt with context if available
    if history_manager.conversation_history:
        recent_context = history_manager.get_history_summary(5)
        enhanced_prompt = f"""{prompt}

IMPORTANT: You are now the DISASTER AGENT. 
Your role is to assess disaster situations and coordinate emergency response. 
You have the following conversation context from the routing agent:

CONVERSATION CONTEXT:
{recent_context}

Continue the conversation as the disaster agent, referencing this context as needed to provide appropriate disaster emergency assistance."""
    else:
        enhanced_prompt = prompt

    chat = create_agent(enhanced_prompt, agent_name)
    print("🔥 Emergency Disaster Agent is active.")
    print(f"💬 Current session has {len(history_manager.conversation_history)} messages")
    print("------------------------------------------------")

    # Process the user input directly
    user_json = {"data": user_input}
    response = mesh_bridge(user_json, chat.send_message, agent_name)
    print("Disaster Agent:", response['data'])
    print(f"🔍 Shared chat history length: {len(chat.history)}")

    # Try to parse JSON response from AI (same logic as original agent)
    agent_result = None
    
    # 1. Check if the response data is already a dictionary
    if isinstance(response['data'], dict):
        agent_result = response['data']
    
    # 2. If it's a string, try to parse it
    elif isinstance(response['data'], str):
        parsed_json = None
        # Try to find and parse a markdown JSON block
        match = re.search(r"```json\s*(\{.*?\})\s*```", response['data'], re.DOTALL)
        if match:
            try:
                parsed_json = json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        
        # If no markdown block was found, try parsing the entire response string as JSON
        if parsed_json is None:
            try:
                parsed_json = json.loads(response['data'])
            except json.JSONDecodeError:
                pass
        
        agent_result = parsed_json

    # 3. Check if we have a valid dictionary containing the specific keys
    if isinstance(agent_result, dict) and 'incident_type' in agent_result and 'summary' in agent_result:
        print("\nAgent: Please stay safe. Emergency services are being dispatched right now.")
        print("✅ Disaster assessment complete. Returning summary.")
        print(agent_result)
        return agent_result
    
    # If no valid JSON structure, generate a fallback incident summary
    incident_summary = {
        "incident_type": "Disaster",
        "summary": f"Disaster incident reported: {user_input}. Agent response: {response['data']}",
        "location": "Location not specified",
        "severity": "high",
        "priority": "CRITICAL"
    }
    
    print("\nAgent: Please stay safe. Emergency services are being dispatched right now.")
    print("✅ Disaster assessment complete. Returning fallback summary.")
    print(incident_summary)
    return incident_summary
