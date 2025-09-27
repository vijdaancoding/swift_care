# HUGELY IMPORTANT: eventlet.monkey_patch() must be called before any other imports
# that might import standard libraries like 'socket' or 'threading'. This includes flask.
import eventlet
eventlet.monkey_patch()

import sys
import io
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from threading import Thread
from queue import Queue

# Now that patching is done, we can import your application logic
from main import main_multi_agent_system

# --- The rest of the script is largely the same ---

app = Flask(__name__)
# Add a secret key for session management, good practice for Flask apps
app.config['SECRET_KEY'] = 'your-very-secret-key!' 
socketio = SocketIO(app, async_mode='eventlet')

# A queue to hold the terminal output
output_queue = Queue()
# A global thread object to ensure we only run the agent system once
agent_thread = None

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

def run_agent_system_with_context(app_context, queue):
    """
    Runs the multi-agent system within a Flask application context
    and redirects its stdout to the queue.
    """
    with app_context:
        # Redirect stdout to our custom queue stream
        original_stdout = sys.stdout
        sys.stdout = QueueIO(queue)
        try:
            main_multi_agent_system()
        except Exception as e:
            print(f"An error occurred in the agent system: {e}")
        finally:
            # Restore original stdout
            sys.stdout = original_stdout
            # Signal the end of the process
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

@app.route('/')
def index():
    """Serve the index page."""
    return render_template('index.html')

@socketio.on('connect')
def on_connect():
    """
    When a client connects, start the agent system if it's not already running.
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
    # We pass the app object to socketio.run
    socketio.run(app, debug=True, port=5000)