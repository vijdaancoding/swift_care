# Emergency Multi-Agent Web Application

This is a Flask web application that provides a user-friendly interface for the Emergency Multi-Agent System. It replicates all the functionality of `main.py` but with a modern web UI.

## Features

- **Split Interface**: Chatbot on the left, orchestration logs on the right
- **Real-time Communication**: Uses WebSockets for live updates
- **Multi-Agent System**: Automatically routes between routing, medical, crime, and disaster agents
- **Session Management**: Tracks conversation history and agent transitions
- **Export Functionality**: Export conversation logs as JSON

## How to Run

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**:
   Make sure you have the required API keys set:
   - `GOOGLE_API_KEY` (for Gemini AI)
   - `GOOGLE_MAPS_API_KEY` (for location services)

3. **Run the Application**:
   ```bash
   python app.py
   ```

4. **Access the Web Interface**:
   Open your browser and go to: `http://localhost:5000`

## Usage

### Starting the System
1. Click the "🚀 Start System" button
2. The system will initialize and show "System Running" status
3. The chatbot interface will become active

### Chatting with Agents
1. Type your emergency description in the chat input
2. The system will automatically route to the appropriate agent:
   - **Routing Agent**: Initial contact, determines incident type
   - **Medical Agent**: Medical emergencies
   - **Crime Agent**: Criminal activities
   - **Disaster Agent**: Natural disasters, fires, etc.

### Monitoring System Activity
- **Left Panel**: Chat interface showing your messages and agent responses
- **Right Panel**: Real-time orchestration logs showing:
  - System status messages
  - Agent transitions
  - Mesh bridge activity
  - Final dispatch reports

### Example Emergency Messages
- "There's been a car accident on Main Street with injuries"
- "Medical emergency - person having chest pains at 123 Elm Street"
- "Armed robbery in progress at First National Bank downtown"
- "Severe flooding reported in residential area, evacuation may be needed"

## System Architecture

The web application maintains the exact same logic as `main.py`:

1. **Agent Flow**: Starts with routing agent → transitions to specialized agents
2. **Mesh Bridge**: Uses the same mesh simulation for message processing
3. **History Management**: Tracks all conversations and agent transitions
4. **Allocator Agent**: Generates final dispatch reports with location data

## API Endpoints

- `GET /` - Main web interface
- `POST /api/system/start` - Start the multi-agent system
- `POST /api/system/stop` - Stop the system
- `GET /api/system/status` - Get current system status
- `POST /api/chat/send` - Send a message to the system
- `GET /api/messages/export` - Export conversation history

## WebSocket Events

- `new_log` - New log entry for orchestration panel
- `agent_changed` - Agent transition notification
- `system_status` - System status updates
- `dispatch_report` - Final dispatch report

## Differences from Terminal Version

- **Input Method**: Web form instead of terminal input
- **Output Display**: Split between chat and logs instead of console output
- **Session Management**: Web-based session tracking
- **Real-time Updates**: Live updates via WebSockets
- **Export Functionality**: Download conversation logs

## Troubleshooting

1. **Import Errors**: Make sure all dependencies are installed
2. **API Key Issues**: Verify environment variables are set correctly
3. **Port Conflicts**: Change the port in `app.py` if 5000 is in use
4. **SocketIO Issues**: The app uses threading mode to avoid eventlet conflicts

## File Structure

```
swift_care/
├── app.py                    # Main Flask application
├── templates/
│   └── emergency_ui.html     # Web interface template
├── agents/                   # Agent modules (unchanged)
├── utils/                    # Utility modules (unchanged)
├── mesh/                     # Mesh simulation (unchanged)
└── prompts/                  # Agent prompts (unchanged)
```

The web application preserves all the original functionality while providing a modern, user-friendly interface for emergency response coordination.
