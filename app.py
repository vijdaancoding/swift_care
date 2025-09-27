import sys
import io
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from threading import Thread
from queue import Queue

# Import your application logic
from main import main_multi_agent_system
from web_agent_system import main_web_agent_system

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-very-secret-key!' 
CORS(app)  # Enable CORS for React app integration
# Use threading mode instead of eventlet for Python 3.13 compatibility
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")

# A queue to hold the terminal output
output_queue = Queue()
# A global thread object to ensure we only run the agent system once
agent_thread = None

# Mock emergency data (matching the React app interface)
mock_emergencies = [
    {
        "id": 1,
        "title": "Cardiac Arrest - DHA Phase 2",
        "priority": "Critical",
        "location": {"lat": 24.8607, "lng": 67.0011},
        "address": "DHA Phase 2, Karachi, Pakistan",
        "description": "Cardiac arrest reported in DHA Phase 2. Patient unconscious, CPR in progress. Ambulance and paramedics dispatched.",
        "timestamp": "2024-01-15T10:28:00Z",
        "type": "medical",
        "status": "active",
        "severity": 9,
        "estimatedDuration": "15-20 min",
        "assignedUnits": ["EMS-101", "FD-Karachi-Engine-54"],
        "contactInfo": {"phone": "+92-21-555-0123"},
        "createdAt": "2024-01-15T10:28:00Z",
        "updatedAt": "2024-01-15T10:28:00Z",
        "reportedBy": {
            "id": 123,
            "name": "John Doe",
            "phone": "+92-21-555-0123"
        }
    },
    {
        "id": 2,
        "title": "Multi-Vehicle Collision - M2 Motorway",
        "priority": "High",
        "location": {"lat": 31.5204, "lng": 74.3587},
        "address": "M2 Motorway, Lahore, Pakistan",
        "description": "Multi-vehicle collision on M2 Motorway. 3 vehicles involved, multiple injuries reported. Traffic backed up for 2 km.",
        "timestamp": "2024-01-15T10:25:00Z",
        "type": "accident",
        "status": "responding",
        "severity": 7,
        "estimatedDuration": "45-60 min",
        "assignedUnits": ["Lahore-Police-19th", "FD-Lahore-Engine-23", "EMS-205"],
        "contactInfo": {"phone": "+92-42-555-0124"},
        "createdAt": "2024-01-15T10:25:00Z",
        "updatedAt": "2024-01-15T10:25:00Z",
        "reportedBy": {
            "id": 124,
            "name": "Sarah Ahmed",
            "phone": "+92-42-555-0124"
        }
    },
    {
        "id": 3,
        "title": "Building Fire - F-8 Sector",
        "priority": "High",
        "location": {"lat": 33.6844, "lng": 73.0479},
        "address": "F-8 Sector, Islamabad, Pakistan",
        "description": "Residential building fire, 4th floor. Smoke visible from street. All residents evacuated. Fire department on scene.",
        "timestamp": "2024-01-15T10:22:00Z",
        "type": "fire",
        "status": "responding",
        "severity": 8,
        "estimatedDuration": "30-45 min",
        "assignedUnits": ["FD-Islamabad-Engine-22", "FD-Islamabad-Ladder-13", "FD-Islamabad-Rescue-1"],
        "contactInfo": {"phone": "+92-51-555-0125"},
        "createdAt": "2024-01-15T10:22:00Z",
        "updatedAt": "2024-01-15T10:22:00Z",
        "reportedBy": {
            "id": 125,
            "name": "Ali Khan",
            "phone": "+92-51-555-0125"
        }
    }
]

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

def run_agent_system_with_context(app_context, queue, user_input=None):
    """
    Runs the multi-agent system within a Flask application context
    and redirects its stdout to the queue.
    """
    with app_context:
        # Redirect stdout to our custom queue stream
        original_stdout = sys.stdout
        sys.stdout = QueueIO(queue)
        try:
            if user_input:
                # Simulate user input by modifying the routing agent input
                print(f"You: {user_input}")
            main_multi_agent_system()
        except Exception as e:
            print(f"An error occurred in the agent system: {e}")
        finally:
            # Restore original stdout
            sys.stdout = original_stdout
            # Signal the end of the process
            queue.put("---END_OF_SESSION---")

def run_web_agent_system_with_context(app_context, queue, user_input):
    """
    Runs the web-compatible multi-agent system within a Flask application context
    and redirects its stdout to the queue.
    """
    with app_context:
        try:
            main_web_agent_system(user_input, queue)
        except Exception as e:
            print(f"An error occurred in the web agent system: {e}")
            queue.put("---END_OF_SESSION---")

def broadcast_output():
    """
    Continuously checks the queue and broadcasts new output to clients.
    """
    while True:
        if not output_queue.empty():
            line = output_queue.get()
            socketio.emit('new_output', {'data': line})
            if line == "---END_OF_SESSION---":
                break # End the broadcast loop
        socketio.sleep(0.1) 

# API Routes for React App
@app.route('/api/v1/emergencies', methods=['GET'])
def get_emergencies():
    """Get all emergencies - API endpoint for React app"""
    return jsonify({
        "success": True,
        "data": {
            "emergencies": mock_emergencies
        }
    })

@app.route('/api/v1/emergencies/<int:emergency_id>/acknowledge', methods=['POST'])
def acknowledge_emergency(emergency_id):
    """Acknowledge an emergency - API endpoint for React app"""
    # Find the emergency
    emergency = next((e for e in mock_emergencies if e['id'] == emergency_id), None)
    if not emergency:
        return jsonify({
            "success": False,
            "error": {
                "code": "EMERGENCY_NOT_FOUND",
                "message": f"Emergency with ID {emergency_id} not found"
            }
        }), 404
    
    # Update status
    emergency['status'] = 'responding'
    emergency['updatedAt'] = datetime.utcnow().isoformat() + 'Z'
    
    return jsonify({
        "success": True,
        "message": f"Emergency {emergency_id} acknowledged successfully"
    })

# Interface Routes
@app.route('/')
def index():
    """Serve the unified interface."""
    return render_template('unified.html')

@app.route('/chatbot')
def chatbot():
    """Serve the chatbot-only interface."""
    return render_template('chatbot.html')

@app.route('/orchestrator')
def orchestrator():
    """Serve the original orchestrator interface."""
    return render_template('index.html')

# WebSocket Events
@socketio.on('connect')
def on_connect():
    """
    When a client connects to the chatbot.
    """
    emit('status', {'data': 'Connected to Swift Care Emergency System'})

@socketio.on('disconnect')
def on_disconnect():
    """
    When a client disconnects.
    """
    print('Client disconnected')

@socketio.on('chat_message')
def handle_chat_message(data):
    """
    Handle chat messages from the chatbot interface.
    """
    user_input = data.get('message', '')
    if user_input.strip():
        print(f"Chat message received: {user_input}")
        
        # Start a new web-compatible agent system session with the user input
        global agent_thread
        app_context = app.app_context()
        agent_thread = socketio.start_background_task(
            target=run_web_agent_system_with_context, 
            app_context=app_context, 
            queue=output_queue,
            user_input=user_input
        )
        # Start the broadcasting thread
        socketio.start_background_task(target=broadcast_output)
        
        emit('agent_response', {'data': 'Processing your emergency report...'})

@socketio.on('orchestrator_connect')
def on_orchestrator_connect():
    """
    When a client connects to the orchestrator interface.
    """
    global agent_thread
    if agent_thread is None or not agent_thread.is_alive():
        print("Client connected. Starting new agent system session...")
        # Start the agent system in a background thread
        app_context = app.app_context()
        agent_thread = socketio.start_background_task(target=run_agent_system_with_context, app_context=app_context, queue=output_queue)
        # Start the broadcasting thread
        socketio.start_background_task(target=broadcast_output)
        emit('status', {'data': 'Connected. Initializing Agent System...'})
    else:
        print("Client reconnected to an ongoing session.")
        emit('status', {'data': 'Reconnected to an ongoing session.'})

if __name__ == '__main__':
    print("Starting Flask-SocketIO server at http://127.0.0.1:5000")
    print("Available routes:")
    print("  - http://127.0.0.1:5000/ (Unified Interface - Chatbot + Orchestrator)")
    print("  - http://127.0.0.1:5000/chatbot (Chatbot Only)")
    print("  - http://127.0.0.1:5000/orchestrator (Orchestrator Only)")
    print("  - http://127.0.0.1:5000/api/v1/emergencies (API for React app)")
    # Use threading mode for Python 3.13 compatibility
    socketio.run(app, debug=True, port=5000, allow_unsafe_werkzeug=True)