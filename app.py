from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
import json
import threading
import time
from datetime import datetime
import uuid
import queue
import sys
import os
import requests

# Add the current directory to Python path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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

app = Flask(__name__)
app.config['SECRET_KEY'] = 'emergency_system_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global state for the system
system_state = {
    'running': False,
    'current_agent': 'routing',
    'session_id': None,
    'message_queue': queue.Queue(),
    'log_queue': queue.Queue(),
    'allocator_agent': None,
    'start_time': None
}

# Agent mapping (same as main.py)
agents = {
    "routing": run_routing_agent,
    "medical": run_medical_agent,
    "crime": run_crime_agent,
    "disaster": run_disaster_agent
}

# Prompt mapping (same as main.py)
prompts = {
    "routing": routing_system_prompt,
    "medical": medical_system_prompt,
    "crime": crime_system_prompt,
    "disaster": disaster_system_prompt
}

def log_message(message_type, content, agent=None):
    """Log a message to be displayed in the orchestration logs"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = {
        'timestamp': timestamp,
        'type': message_type,
        'content': content,
        'agent': agent
    }
    system_state['log_queue'].put(log_entry)
    
    # Emit to all connected clients
    socketio.emit('new_log', log_entry)

def process_user_message(message):
    """Process user message through the multi-agent system"""
    try:
        current_agent = system_state['current_agent']
        
        log_message('user', f"You: {message}", current_agent)
        
        if current_agent.lower() in agents:
            # Create a modified version of the agent that works with our UI
            result = run_agent_with_ui(current_agent.lower(), message)
            
            if isinstance(result, dict) and "incident_type" in result:
                # Forward to allocator agent
                log_message('system', "\nForwarding incident summary to Allocator Agent...", 'allocator')
                
                if system_state['allocator_agent'] is None:
                    system_state['allocator_agent'] = AllocatorAgent(maps_api_key, api_key)
                
                allocation_result = system_state['allocator_agent'].process_incident(result)
                
                log_message('dispatch', f"\n DISPATCH REPORT:\n{json.dumps(allocation_result, indent=2)}", 'allocator')
                
                # Send dispatch report to React frontend
                send_dispatch_to_frontend(allocation_result)
                
                # End the session
                system_state['current_agent'] = None
                system_state['running'] = False
                
                # Emit final dispatch report
                socketio.emit('dispatch_report', allocation_result)
                
            else:
                # Agent wants to transition to another agent
                new_agent = result.lower() if result else None
                if new_agent and new_agent != current_agent:
                    add_agent_transition(current_agent, new_agent, "System routing")
                    system_state['current_agent'] = new_agent
                    
                    log_message('system', f"\nRouting complete. Handing off to {new_agent} agent...\n", 'system')
                    socketio.emit('agent_changed', {
                        'old_agent': current_agent,
                        'new_agent': new_agent,
                        'transitions': len(history_manager.agent_transitions)
                    })
                elif new_agent is None:
                    # Agent is continuing conversation (no transition needed)
                    log_message('system', f"Continuing conversation with {current_agent} agent...", 'system')
                    # Keep the current agent and system running
        else:
            log_message('error', f"Unknown agent: {current_agent}", 'system')
            system_state['running'] = False
            
    except Exception as e:
        log_message('error', f"Error processing message: {str(e)}", 'system')
        print(f"Error in process_user_message: {e}")

def run_agent_with_ui(agent_name, user_message):
    """Run an agent with UI integration instead of terminal input"""
    from utils.agent_creation import create_agent
    from mesh.main_simulation import mesh_bridge
    
    # Get the prompt for this agent
    prompt = prompts[agent_name]
    
    # Create agent
    chat = create_agent(prompt, agent_name)
    
    log_message('system', f"{agent_name.title()} Agent is active.", agent_name)
    
    # Process the user message
    user_json = {
        "data": user_message
    }
    
    response = mesh_bridge(user_json, chat.send_message, agent_name)
    agent_response = response['data']
    
    log_message('agent', f"{agent_name.title()} Agent: {agent_response}", agent_name)
    
    # Send agent response to chat interface
    socketio.emit('agent_response', {
        'agent': agent_name,
        'message': agent_response,
        'timestamp': datetime.now().strftime("%H:%M:%S")
    })
    
    # Check if this agent wants to route to another agent
    if "ROUTE:" in agent_response:
        category = agent_response.split("ROUTE:")[-1].strip()
        log_message('system', f"Routing decision detected: {category}", agent_name)
        return category
    else:
        log_message('system', f"No routing decision - continuing with {agent_name} agent", agent_name)
    
    # Check if this is an incident report (medical, crime, disaster agents)
    if agent_name in ['medical', 'crime', 'disaster']:
        # Try to extract incident information
        try:
            incident_data = extract_incident_data(agent_response, agent_name, user_message)
            if incident_data:
                return incident_data
        except Exception as e:
            log_message('error', f"Error extracting incident data: {e}", agent_name)
    
    return None

def extract_incident_data(agent_response, agent_type, user_message):
    """Extract incident data from agent response"""
    # This is a simplified extraction - in reality, you might want more sophisticated parsing
    incident_types = {
        'medical': 'Medical',
        'crime': 'Crime', 
        'disaster': 'Disaster'
    }
    
    # Try to extract location from user message (simple keyword matching)
    location_keywords = ['at', 'on', 'near', 'in']
    location = "Unknown location"
    for keyword in location_keywords:
        if keyword in user_message.lower():
            parts = user_message.lower().split(keyword)
            if len(parts) > 1:
                location = parts[1].strip().title()
                break
    
    incident_data = {
        "incident_type": incident_types.get(agent_type, "Unknown"),
        "location": location,
        "summary": f"{agent_type.title()} incident: {agent_response}",
        "details": user_message
    }
    
    return incident_data

def send_dispatch_to_frontend(dispatch_data):
    """Send dispatch report to React frontend"""
    try:
        # Frontend bridge server URL - use local bridge server
        # The bridge server will handle sending to the deployed React app
        frontend_url = "http://localhost:3001"
        
        # Prepare data in the format expected by React frontend
        emergency_data = {
            "success": True,
            "data": {
                "emergencies": [dispatch_data]
            }
        }
        
        # Send POST request to React frontend
        # You might need to create an endpoint in your React app to receive this
        response = requests.post(
            f"{frontend_url}/api/emergencies/receive-dispatch",
            json=emergency_data,
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        
        if response.status_code == 200:
            log_message('system', f"Dispatch report sent to React frontend successfully", 'system')
            print(f"Dispatch sent to frontend: {response.status_code}")
        else:
            log_message('error', f"Failed to send dispatch to frontend: {response.status_code}", 'system')
            print(f"Frontend request failed: {response.status_code} - {response.text}")
            
    except requests.exceptions.RequestException as e:
        log_message('error', f"Could not connect to React frontend: {str(e)}", 'system')
        print(f"Frontend connection error: {e}")
    except Exception as e:
        log_message('error', f"Error sending dispatch to frontend: {str(e)}", 'system')
        print(f"Frontend send error: {e}")

@app.route('/')
def index():
    return render_template('emergency_ui.html')

@app.route('/debug')
def debug():
    return render_template('debug.html')

@app.route('/api/system/start', methods=['POST'])
def start_system():
    """Start the multi-agent system"""
    if system_state['running']:
        return jsonify({'success': False, 'error': 'System already running'})
    
    try:
        # Initialize new session
        start_new_session()
        system_state['session_id'] = history_manager.current_session_id
        system_state['running'] = True
        system_state['current_agent'] = 'routing'
        system_state['start_time'] = time.time()
        
        log_message('system', "Multi-Agent Emergency System Started", 'system')
        log_message('system', "Centralized history management active", 'system')
        log_message('system', "="*60, 'system')
        
        # Get initial stats
        stats = history_manager.get_stats()
        
        return jsonify({
            'success': True,
            'session_id': system_state['session_id'],
            'current_agent': system_state['current_agent'],
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/system/stop', methods=['POST'])
def stop_system():
    """Stop the multi-agent system"""
    if not system_state['running']:
        return jsonify({'success': False, 'error': 'System not running'})
    
    try:
        system_state['running'] = False
        system_state['current_agent'] = None
        
        # Print final session summary
        log_message('system', "\n" + "="*60, 'system')
        log_message('system', "SESSION SUMMARY", 'system')
        log_message('system', "="*60, 'system')
        
        stats = history_manager.get_stats()
        log_message('system', f"Session ID: {stats['session_id']}", 'system')
        log_message('system', f"Total Messages: {stats['total_messages']}", 'system')
        log_message('system', f"Agent Transitions: {stats['agent_transitions']}", 'system')
        log_message('system', f"Agents Used: {', '.join(stats['agents_used']) if stats['agents_used'] else 'None'}", 'system')
        
        log_message('system', "\nEmergency system session ended.", 'system')
        log_message('system', "="*60, 'system')
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/system/status', methods=['GET'])
def get_system_status():
    """Get current system status"""
    stats = history_manager.get_stats()
    duration = 0
    if system_state['start_time']:
        duration = int(time.time() - system_state['start_time'])
    
    return jsonify({
        'running': system_state['running'],
        'session_id': system_state['session_id'],
        'current_agent': system_state['current_agent'],
        'message_count': stats['total_messages'],
        'agent_transitions': stats['agent_transitions'],
        'duration': duration
    })

@app.route('/api/system/send-dummy', methods=['POST'])
def send_dummy_data():
    """Send dummy emergency data to test frontend connection"""
    try:
        dummy_data = request.get_json()
        
        if not dummy_data or 'data' not in dummy_data:
            return jsonify({
                'success': False,
                'message': 'Invalid dummy data format'
            }), 400
        
        log_message('test', f"Sending dummy emergency data to frontend", 'system')
        log_message('test', f"Dummy emergency ID: {dummy_data['data']['emergencies'][0]['id']}", 'system')
        
        # Send to frontend bridge server
        send_dispatch_to_frontend(dummy_data['data']['emergencies'][0])
        
        return jsonify({
            'success': True,
            'message': 'Dummy data sent successfully',
            'emergency_id': dummy_data['data']['emergencies'][0]['id']
        })
        
    except Exception as e:
        log_message('error', f"Error sending dummy data: {str(e)}", 'system')
        return jsonify({
            'success': False,
            'message': f'Error sending dummy data: {str(e)}'
        }), 500

@app.route('/api/chat/send', methods=['POST'])
def send_chat_message():
    """Send a chat message to the system"""
    if not system_state['running']:
        return jsonify({'success': False, 'error': 'System not running'})
    
    data = request.get_json()
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'success': False, 'error': 'Empty message'})
    
    # Process the message in a separate thread to avoid blocking
    threading.Thread(target=process_user_message, args=(message,)).start()
    
    return jsonify({
        'success': True,
        'agent': system_state['current_agent']
    })

@app.route('/api/messages/export', methods=['GET'])
def export_messages():
    """Export conversation history"""
    stats = history_manager.get_stats()
    export_data = {
        'session_id': system_state['session_id'],
        'export_time': datetime.now().isoformat(),
        'stats': stats,
        'conversation_history': history_manager.conversation_history,
        'agent_transitions': history_manager.agent_transitions
    }
    
    return jsonify(export_data)

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('connected', {'message': 'Connected to emergency system'})
    
    # Send current system status
    stats = history_manager.get_stats()
    emit('system_status', {
        'running': system_state['running'],
        'session_id': system_state['session_id'],
        'current_agent': system_state['current_agent'],
        'message_count': stats['total_messages'],
        'agent_transitions': stats['agent_transitions']
    })

@socketio.on('test')
def handle_test(data):
    """Handle test message"""
    emit('test_response', f'Server received: {data}')

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')

if __name__ == '__main__':
    print("Starting Emergency Multi-Agent Web System")
    print("Web UI will be available at http://localhost:5000")
    print("Chat interface on the left, orchestration logs on the right")
    print("="*60)
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
