"""
Web-compatible version of the multi-agent system that accepts input from WebSocket
instead of terminal input.
"""

from web_agents import run_routing_agent_web, run_medical_agent_web, run_crime_agent_web, run_disaster_agent_web
from agents.allocator_agent import AllocatorAgent
from prompts.routing_prompt import routing_system_prompt
from prompts.medical_prompt import medical_system_prompt
from prompts.crime_prompt import crime_system_prompt
from prompts.disaster_prompt import disaster_system_prompt
from utils.global_history import start_new_session, history_manager, add_agent_transition
from utils.agent_creation import maps_api_key, api_key
from queue import Queue
import sys
import io

class QueueIO(io.StringIO):
    """A custom file-like object that writes to a queue."""
    def __init__(self, queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = queue

    def write(self, s):
        # Write to the queue for broadcasting
        self.queue.put(s)
        # Also write to the actual stdout so you can see it in the terminal where you run flask
        sys.__stdout__.write(s)
        super().write(s)

    def flush(self):
        sys.__stdout__.flush()
        super().flush()

def main_web_agent_system(user_input, output_queue):
    """
    Web-compatible multi-agent system that processes a single user input
    and returns the complete response flow.
    """
    # Initialize new session
    start_new_session()
    
    # Redirect stdout to our custom queue stream
    original_stdout = sys.stdout
    sys.stdout = QueueIO(output_queue)
    
    try:
        print("🚀 Multi-Agent Emergency System Started")
        print("🔄 Centralized history management active")
        print("="*60)
        
        current_agent = "routing"
        previous_agent = None
        allocator_agent = AllocatorAgent(maps_api_key, api_key)
        
        # Agent mapping
        agents = {
            "routing": run_routing_agent_web,
            "medical": run_medical_agent_web,
            "crime": run_crime_agent_web,
            "disaster": run_disaster_agent_web
        }
        
        # Prompt mapping
        prompts = {
            "routing": routing_system_prompt,
            "medical": medical_system_prompt,
            "crime": crime_system_prompt,
            "disaster": disaster_system_prompt
        }
        
        # Process through the agent workflow (same logic as main.py)
        while current_agent:
            print(f"\n🔄 Current Agent: {current_agent.title()}")
            
            if current_agent.lower() in agents:
                # Record transition if not the first agent
                if previous_agent and previous_agent != current_agent:
                    add_agent_transition(previous_agent, current_agent, "System routing")
                
                # Run the agent with the user input (only for routing agent)
                if current_agent.lower() == "routing":
                    result = agents[current_agent.lower()](prompts[current_agent.lower()], user_input)
                else:
                    # For other agents, use the original input for context
                    result = agents[current_agent.lower()](prompts[current_agent.lower()], user_input)
            
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
                    previous_agent = current_agent
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
        
    except Exception as e:
        print(f"An error occurred in the agent system: {e}")
    finally:
        # Restore original stdout
        sys.stdout = original_stdout
        # Signal the end of the process
        output_queue.put("---END_OF_SESSION---")
