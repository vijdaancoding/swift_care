from agents.routing_agent import run_routing_agent
from agents.medical_agent import run_medical_agent
from agents.crime_agent import run_crime_agent
from agents.disaster_agent import run_disaster_agent
from agents.allocator_agent import AllocatorAgent
from prompts.routing_prompt import routing_system_prompt
from prompts.medical_prompt import medical_system_prompt
from prompts.crime_prompt import crime_system_prompt
from prompts.disaster_prompt import disaster_system_prompt
from utils.global_history import start_new_session, history_manager, add_agent_transition

from utils.agent_creation import maps_api_key, api_key

import re 
import json

def main_multi_agent_system():
    """
    Main system with centralized history management
    """
    # Initialize new session
    start_new_session()
    
    print("🚀 Multi-Agent Emergency System Started")
    print("🔄 Centralized history management active")
    print("="*60)
    
    current_agent = "routing"
    previous_agent = None
    allocator_agent = AllocatorAgent(maps_api_key, api_key)
    
    # Agent mapping
    agents = {
        "routing": run_routing_agent,
        "medical": run_medical_agent,
        "crime": run_crime_agent,
        "disaster": run_disaster_agent
    }
    
    # Prompt mapping
    prompts = {
        "routing": routing_system_prompt,
        "medical": medical_system_prompt,
        "crime": crime_system_prompt,
        "disaster": disaster_system_prompt
    }
    
    while current_agent:
        print(f"\n🔄 Current Agent: {current_agent.title()}")
        
        if current_agent.lower() in agents:
            # Record transition if not the first agent
            if previous_agent and previous_agent != current_agent:
                add_agent_transition(previous_agent, current_agent, "System routing")
            
            # Run the agent
            result = agents[current_agent.lower()](prompts[current_agent.lower()])
        

            if isinstance(result, dict) and "incident_type" in result:
                print("\nForwarding incident summary to Allocator Agent...")
                allocation_result = allocator_agent.process_incident(result)

                print(f"\n DISPATCH REPORT:")
                print(f"  Location: {allocation_result['location_reported']}")

                if allocation_result['facility_found']:
                    facility = allocation_result['nearest_facility']
                    print(f"  Target: {facility['name']} ({facility['distance_km']} km)")
                else:
                    print(f"  Target: Standard Emergency Response")
            
                print(f"  Action: {allocation_result['ai_recommendation']}")
                print(f"  Status: {allocation_result['processing_status'].upper()}")

                current_agent = None
            else:
                current_agent = result.lower() if result else None
                
        else:
            print(f"❌ Unknown agent: {current_agent}")
            print("Available agents:", list(agents.keys()))
            current_agent = None
    
    # Print final session summary
    print("\n" + "="*60)
    print("📊 SESSION SUMMARY")
    print("="*60)
    
    stats = history_manager.get_stats()
    print(f"Session ID: {stats['session_id']}")
    print(f"Total Messages: {stats['total_messages']}")
    print(f"Agent Transitions: {stats['agent_transitions']}")
    print(f"Agents Used: {', '.join(stats['agents_used']) if stats['agents_used'] else 'None'}")
    
    # Show recent conversation
    if history_manager.conversation_history:
        print(f"\nFinal Conversation Context:")
        recent_summary = history_manager.get_history_summary(5)
        for line in recent_summary.split('\n'):
            print(f"  {line}")
    
    print("\n👋 Emergency system session ended.")
    print("="*60)

if __name__ == "__main__":
    main_multi_agent_system()