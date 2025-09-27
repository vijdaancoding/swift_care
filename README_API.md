# Swift Care Flask API Server

This Flask application provides both API endpoints for the React frontend and a chatbot interface for emergency reporting.

## Features

- **REST API Endpoints** for the React emergency dashboard
- **Real-time Chatbot Interface** with WebSocket support
- **Multi-Agent Emergency Processing** integration
- **CORS Support** for frontend integration

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure all the agent files are in place (agents/, prompts/, utils/, etc.)

## Running the Server

```bash
python app.py
```

The server will start on `http://127.0.0.1:5000`

## Available Routes

### Web Interfaces
- `/` - Chatbot interface for emergency reporting
- `/orchestrator` - Original multi-agent orchestrator interface

### API Endpoints (for React app)
- `GET /api/v1/emergencies` - Get all emergencies
- `POST /api/v1/emergencies/{id}/acknowledge` - Acknowledge an emergency

## API Documentation

### GET /api/v1/emergencies

Returns a list of all emergencies.

**Response:**
```json
{
  "success": true,
  "data": {
    "emergencies": [
      {
        "id": 1,
        "title": "Cardiac Arrest - DHA Phase 2",
        "priority": "Critical",
        "location": {"lat": 24.8607, "lng": 67.0011},
        "address": "DHA Phase 2, Karachi, Pakistan",
        "description": "Cardiac arrest reported...",
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
      }
    ]
  }
}
```

### POST /api/v1/emergencies/{id}/acknowledge

Acknowledges an emergency and updates its status to "responding".

**Response (Success):**
```json
{
  "success": true,
  "message": "Emergency 1 acknowledged successfully"
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": {
    "code": "EMERGENCY_NOT_FOUND",
    "message": "Emergency with ID 999 not found"
  }
}
```

## Chatbot Interface

The chatbot interface allows users to report emergencies through natural language. The system processes these reports through the multi-agent workflow:

1. **User Input** - User describes their emergency
2. **Routing Agent** - Classifies the emergency type
3. **Specialized Agent** - Medical, Crime, Disaster, or Fire agent processes the case
4. **Allocator Agent** - Finds nearest facilities and generates dispatch report
5. **Response** - User receives dispatch information

### WebSocket Events

- `chat_message` - Send a message to the chatbot
- `new_output` - Receive agent system output
- `agent_response` - Receive system responses
- `status` - Connection status updates

## Testing

Run the test script to verify API endpoints:

```bash
python test_api.py
```

Make sure the Flask server is running before testing.

## Integration with React App

The React app can now connect to these endpoints:

```typescript
// Fetch emergencies
const response = await fetch('http://127.0.0.1:5000/api/v1/emergencies');
const data = await response.json();

// Acknowledge emergency
const ackResponse = await fetch(`http://127.0.0.1:5000/api/v1/emergencies/${id}/acknowledge`, {
  method: 'POST'
});
```

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React App     │    │   Flask API      │    │  Agent System   │
│                 │◄──►│                  │◄──►│                 │
│ - Dashboard     │    │ - REST Endpoints │    │ - Routing Agent │
│ - Map View      │    │ - Chatbot UI     │    │ - Medical Agent │
│ - Emergency UI  │    │ - WebSocket      │    │ - Crime Agent   │
└─────────────────┘    └──────────────────┘    │ - Disaster Agent│
                                               │ - Allocator     │
                                               └─────────────────┘
```

## Development

- The Flask app runs on port 5000 by default
- CORS is enabled for development
- WebSocket events are handled with Socket.IO
- The agent system runs in background threads

## Production Considerations

- Use a production WSGI server like Gunicorn
- Set up proper authentication for API endpoints
- Configure HTTPS for security
- Use environment variables for sensitive data
- Set up proper logging and monitoring
