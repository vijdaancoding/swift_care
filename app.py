from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import threading
import time
import json
import uuid
from datetime import datetime
from queue import Queue
import sys
import os

# Import your existing agents (adjust paths as needed)
try:
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
except ImportError as e:
    print(f"Warning: Could not import agents: {e}")
    print("Running in demo mode")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'emergency_system_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state
system_state = {
    'running': False,
    'current_agent': 'routing',
    'session_id': None,
    'start_time': None,
    'message_count': 0,
    'agent_transitions': 0,
    'agents_used': set(),
    'message_queue': Queue(),
    'user_input_queue': Queue()
}

class UILogger:
    """Custom logger that sends messages to the web UI"""
    
    def __init__(self):
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
    
    def log_message(self, message_type, content, agent=None):
        """Send a message to the UI via WebSocket"""
        message_data = {
            'type': message_type,
            'content': str(content),
            'agent': agent,
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'session_id': system_state['session_id']
        }
        
        system_state['message_count'] += 1
        if agent:
            system_state['agents_used'].add(agent)
        
        # Emit to all connected clients
        socketio.emit('new_message', message_data)
        
        # Store in queue for persistence
        system_state['message_queue'].put(message_data)
        
        return message_data
    
    def write(self, text):
        """Intercept stdout/stderr and send to UI"""
        if text.strip():
            self.log_message('system', text.strip())
        # Also write to original stdout for console logging
        self.original_stdout.write(text)
    
    def flush(self):
        self.original_stdout.flush()

ui_logger = UILogger()

@app.route('/')
def index():
    """Serve the main UI"""
    return render_template('index.html')

@app.route('/api/system/start', methods=['POST'])
def start_system():
    """Start the emergency system"""
    if system_state['running']:
        return jsonify({'error': 'System already running'}), 400
    
    try:
        # Initialize system
        system_state['running'] = True
        system_state['session_id'] = f"ES_{str(uuid.uuid4())[:8]}"
        system_state['start_time'] = datetime.now()
        system_state['message_count'] = 0
        system_state['agent_transitions'] = 0
        system_state['agents_used'] = set()
        system_state['current_agent'] = 'routing'
        
        # Start new session
        try:
            start_new_session()
        except:
            pass  # In case imports failed
        
        ui_logger.log_message('system', '🚀 Multi-Agent Emergency System Started')
        ui_logger.log_message('system', '🔄 Centralized history management active')
        ui_logger.log_message('system', '=' * 60)
        
        # Start the agent system in a separate thread
        agent_thread = threading.Thread(target=run_agent_system, daemon=True)
        agent_thread.start()
        
        return jsonify({
            'success': True,
            'session_id': system_state['session_id'],
            'message': 'System started successfully'
        })
        
    except Exception as e:
        system_state['running'] = False
        return jsonify({'error': f'Failed to start system: {str(e)}'}), 500

@app.route('/api/system/stop', methods=['POST'])
def stop_system():
    """Stop the emergency system"""
    if not system_state['running']:
        return jsonify({'error': 'System not running'}), 400
    
    system_state['running'] = False
    system_state['user_input_queue'].put(None) 
    # Generate session summary
    duration = datetime.now() - system_state['start_time'] if system_state['start_time'] else 0
    summary = f"""
📊 SESSION SUMMARY
{'=' * 60}
Session ID: {system_state['session_id']}
Total Messages: {system_state['message_count']}
Agent Transitions: {system_state['agent_transitions']}
Agents Used: {', '.join(system_state['agents_used']) if system_state['agents_used'] else 'None'}
Duration: {duration}

👋 Emergency system session ended.
{'=' * 60}
"""
    
    ui_logger.log_message('system', summary)
    
    return jsonify({
        'success': True,
        'message': 'System stopped successfully',
        'summary': {
            'session_id': system_state['session_id'],
            'total_messages': system_state['message_count'],
            'agent_transitions': system_state['agent_transitions'],
            'agents_used': list(system_state['agents_used']),
            'duration': str(duration)
        }
    })

@app.route('/api/system/status')
def get_status():
    """Get current system status"""
    duration = 0
    if system_state['running'] and system_state['start_time']:
        duration = (datetime.now() - system_state['start_time']).total_seconds()
    
    return jsonify({
        'running': system_state['running'],
        'current_agent': system_state['current_agent'],
        'session_id': system_state['session_id'],
        'message_count': system_state['message_count'],
        'agent_transitions': system_state['agent_transitions'],
        'agents_used': list(system_state['agents_used']),
        'duration': int(duration)
    })

@app.route('/api/messages/export')
def export_messages():
    """Export all messages as JSON"""
    messages = []
    temp_queue = Queue()
    
    # Extract messages from queue
    while not system_state['message_queue'].empty():
        msg = system_state['message_queue'].get()
        messages.append(msg)
        temp_queue.put(msg)  # Put back for persistence
    
    # Restore queue
    while not temp_queue.empty():
        system_state['message_queue'].put(temp_queue.get())
    
    return jsonify({
        'session_id': system_state['session_id'],
        'export_time': datetime.now().isoformat(),
        'total_messages': len(messages),
        'messages': messages
    })

@app.route('/api/agent/switch', methods=['POST'])
def switch_agent():
    """Switch to a different agent"""
    data = request.get_json()
    new_agent = data.get('agent', '').lower()
    
    valid_agents = ['routing', 'medical', 'crime', 'disaster']
    if new_agent not in valid_agents:
        return jsonify({'error': f'Invalid agent. Must be one of: {valid_agents}'}), 400
    
    old_agent = system_state['current_agent']
    system_state['current_agent'] = new_agent
    
    if old_agent != new_agent:
        system_state['agent_transitions'] += 1
        try:
            add_agent_transition(old_agent, new_agent, "Manual switch")
        except:
            pass
        
        ui_logger.log_message('system', f'🔄 Agent Transition: {old_agent} → {new_agent}')
    
    # Emit agent change to all clients
    socketio.emit('agent_changed', {
        'old_agent': old_agent,
        'new_agent': new_agent,
        'transitions': system_state['agent_transitions']
    })
    
    return jsonify({'success': True, 'current_agent': new_agent})

@app.route('/api/chat/send', methods=['POST'])
def send_chat_message():
    """Handle incoming chat messages from the user"""
    if not system_state['running']:
        return jsonify({'error': 'System is not running. Cannot send message.'}), 400

    data = request.get_json()
    message_content = data.get('message')

    if not message_content:
        return jsonify({'error': 'Message content is empty'}), 400

    # Log the user's message to the UI so it appears instantly
    ui_logger.log_message('user', message_content, agent=system_state['current_agent'])

    # Put the message into the queue for the agent thread to process
    system_state['user_input_queue'].put(message_content)

    return jsonify({
        'success': True,
        'message': 'Message received for processing',
        'agent': system_state['current_agent']
    })

def run_agent_system():
    """Run the main agent system, now driven by user input from a queue."""
    # Agent and prompt mappings (assuming these are defined as before)
    agents = {
        "routing": run_routing_agent, "medical": run_medical_agent,
        "crime": run_crime_agent, "disaster": run_disaster_agent
    }
    prompts = {
        "routing": routing_system_prompt, "medical": medical_system_prompt,
        "crime": crime_system_prompt, "disaster": disaster_system_prompt
    }

    try:
        allocator_agent = AllocatorAgent(maps_api_key, api_key)
    except NameError:
        allocator_agent = None
        ui_logger.log_message('error', 'Could not initialize AllocatorAgent - running in demo mode')

    while system_state['running']:
        try:
            # Block and wait for the next user message from the queue
            ui_logger.log_message('system', "Awaiting user input...")
            user_input = system_state['user_input_queue'].get()

            # If we receive None, it's a signal to shut down
            if user_input is None:
                continue

            current_agent = system_state['current_agent']
            previous_agent = None

            # Keep processing as long as agents are routing to each other
            while current_agent and system_state['running']:
                ui_logger.log_message('system', f"\n🔄 Current Agent: {current_agent.title()}")
                system_state['current_agent'] = current_agent
                socketio.emit('agent_changed', {'new_agent': current_agent, 'transitions': system_state['agent_transitions']})

                if current_agent.lower() not in agents:
                    ui_logger.log_message('error', f"❌ Unknown agent: {current_agent}")
                    break

                # The first agent in a chain gets the direct user input
                # Subsequent agents rely on the shared history.
                agent_input = user_input if previous_agent is None else None

                ui_logger.log_message('agent', f"Running {current_agent} agent...", current_agent)

                # --- This is the key change to pass input to your agent ---
                # Your agent function now receives the user input
                result = agents[current_agent.lower()](prompts[current_agent.lower()], agent_input)
                # ---------------------------------------------------------

                # Check if the agent returned a final incident report
                if isinstance(result, dict) and "incident_type" in result:
                    ui_logger.log_message('system', "\nForwarding incident summary to Allocator Agent...")
                    if allocator_agent:
                        allocation_result = allocator_agent.process_incident(result)
                        dispatch_report = f"""DISPATCH REPORT:
                        Location: {allocation_result['location_reported']}
Target: {allocation_result['nearest_facility']['name'] if allocation_result['facility_found'] else 'Standard Emergency Response'} {f"({allocation_result['nearest_facility']['distance_km']} km)" if allocation_result['facility_found'] else ''}
Action: {allocation_result['ai_recommendation']}
Status: {allocation_result['processing_status'].upper()}                        
"""
                        ui_logger.log_message('dispatch', dispatch_report)
                    else:
                        ui_logger.log_message('dispatch', "🚨 DISPATCH REPORT:\n  Status: SIMULATED")
                    current_agent = None # End of this interaction
                else:
                    # Otherwise, transition to the next agent
                    previous_agent = current_agent
                    current_agent = result.lower() if result else None
                    if previous_agent and current_agent and previous_agent != current_agent:
                        system_state['agent_transitions'] += 1
                        try:
                            add_agent_transition(previous_agent, current_agent, "System routing")
                        except NameError: pass

                time.sleep(1)

        except Exception as e:
            ui_logger.log_message('error', f"Error in agent processing loop: {str(e)}")
            # Reset for next input
            system_state['current_agent'] = 'routing'

    ui_logger.log_message('system', "Agent processing thread has stopped.")

def simulate_agent_behavior(agent_name):
    """Simulate agent behavior when real agents aren't available"""
    import random
    
    scenarios = {
        'routing': [
            "📞 Emergency call received\n📍 Analyzing location and incident type\n🔄 Routing to appropriate specialist agent",
            "🆘 Multiple emergency reports detected\n📊 Prioritizing based on severity\n➡️ Dispatching to medical agent"
        ],
        'medical': [
            "🏥 Medical emergency analysis complete\n🚑 Requesting ambulance dispatch\n📍 Location: Downtown Medical Center\n⏱️ ETA: 12 minutes",
            "🩺 Patient vitals assessment\n🔴 Critical condition detected\n🚁 Helicopter medical transport requested"
        ],
        'crime': [
            "👮 Crime incident verification\n🚔 Police units dispatched\n📍 Securing perimeter at Oak Street\n⚠️ Suspect description broadcasted",
            "🔍 Investigation protocols initiated\n📝 Witness statements being collected\n🚓 Additional backup units requested"
        ],
        'disaster': [
            "🌪️ Weather alert system activated\n📢 Emergency broadcast initiated\n🏠 Evacuation procedures for Zone 7\n🚨 All emergency services coordinated",
            "⚡ Power grid failure detected\n🔧 Utility companies notified\n🏥 Hospital backup generators confirmed\n📱 Emergency communication channels active"
        ]
    }
    
    # Simulate some processing time
    time.sleep(2)
    
    # Select random scenario
    scenario = random.choice(scenarios.get(agent_name, ["Generic emergency response initiated"]))
    ui_logger.log_message('agent', scenario, agent_name)
    
    # Sometimes route to another agent, sometimes complete
    if random.random() < 0.3:  # 30% chance to route to another agent
        agents = ['medical', 'crime', 'disaster']
        agents.remove(agent_name) if agent_name in agents else None
        return random.choice(agents) if agents else None
    else:
        # Return incident summary to trigger dispatch
        return {
            'incident_type': agent_name,
            'location': f"{random.randint(100, 999)} Main Street",
            'severity': random.choice(['low', 'medium', 'high', 'critical']),
            'description': scenario
        }

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('system_status', {
        'running': system_state['running'],
        'current_agent': system_state['current_agent'],
        'session_id': system_state['session_id']
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    pass

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    print("🚀 Starting Emergency System Flask App...")
    print("📱 Web UI will be available at: http://localhost:5000")
    print("🔧 Socket.IO enabled for real-time updates")
    print("=" * 60)
    
    # Run the Flask app with Socket.IO
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)