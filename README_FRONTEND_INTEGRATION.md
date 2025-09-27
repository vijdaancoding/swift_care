# Frontend Integration Setup

This guide explains how to connect the Flask emergency system with your React frontend.

## Architecture Overview

```
Flask Backend (Port 5000) → Frontend Bridge (Port 3001) → React Frontend (Port 3000)
                                                      ↘ Deployed React App (Vercel)
```

**Deployed React App**: https://stratagem-react.vercel.app/

## Setup Instructions

### 1. Start the Flask Backend
```bash
cd swift_care
python app.py
```
- Runs on: `http://localhost:5000`
- Emergency chat interface available here

### 2. Start the Frontend Bridge Server
```bash
cd swift_care
npm install
npm start
```
- Runs on: `http://localhost:3001`
- Receives dispatch reports from Flask
- Provides API endpoints for React frontend

### 3. Start Your React Frontend (Optional - for local development)
```bash
cd stratagem-react
npm start
```
- Runs on: `http://localhost:3000`
- Your main emergency management dashboard

### 4. Access Deployed React App
- **Production URL**: https://stratagem-react.vercel.app/
- The bridge server will automatically send dispatch reports to this deployed app

## API Endpoints

### Frontend Bridge Server (Port 3001)

#### Receive Dispatch Report (from Flask)
- **POST** `/api/emergencies/receive-dispatch`
- Receives emergency data from Flask backend
- Called automatically when dispatch report is generated

#### Get Emergencies (for React)
- **GET** `/api/v1/emergencies`
- Returns all emergencies in the format expected by your React app

#### Acknowledge Emergency
- **POST** `/api/v1/emergencies/:id/acknowledge`
- Marks an emergency as "responding"

#### Real-time Updates
- **GET** `/api/emergencies/stream`
- Server-Sent Events for real-time emergency notifications

## Data Flow

1. **User reports emergency** via Flask chat interface
2. **Agents process** the emergency (routing → specialized agent → allocator)
3. **Allocator generates** dispatch report in React-compatible format
4. **Flask sends** dispatch report to frontend bridge server
5. **Bridge server** stores emergency and broadcasts to React frontend
6. **React frontend** receives real-time emergency notifications

## Emergency Data Format

The system sends data in the exact format expected by your React frontend:

```typescript
interface Emergency {
  id: number;
  title: string;
  priority: 'Critical' | 'High' | 'Medium' | 'Low';
  location: { lat: number; lng: number; };
  address: string;
  description: string;
  timestamp: string;
  type: 'medical' | 'fire' | 'accident' | 'police' | 'other';
  status: 'active' | 'responding' | 'resolved' | 'cancelled';
  severity: number; // 1-10 scale
  estimatedDuration?: string;
  assignedUnits?: string[];
  contactInfo?: { phone?: string; email?: string; };
  createdAt: string;
  updatedAt: string;
  reportedBy: { id: number; name: string; phone?: string; };
  images?: string[];
  audio?: string;
  video?: string;
}
```

## React Frontend Integration

### Option 1: Poll for New Emergencies (Recommended for Vercel)

Since Vercel doesn't support Server-Sent Events in the same way, you can poll for new emergencies:

```javascript
// In your React component
useEffect(() => {
  const fetchEmergencies = async () => {
    try {
      const response = await fetch('http://localhost:3001/api/v1/emergencies');
      const data = await response.json();
      setEmergencies(data.data.emergencies);
    } catch (error) {
      console.error('Error fetching emergencies:', error);
    }
  };

  // Fetch initially
  fetchEmergencies();
  
  // Poll every 5 seconds for new emergencies
  const interval = setInterval(fetchEmergencies, 5000);
  
  return () => clearInterval(interval);
}, []);
```

### Option 2: Create API Route in React App (Advanced)

If you want real-time updates, you can create an API route in your React app to receive dispatch reports directly:

1. Create `pages/api/emergencies/receive.js` (for Next.js) or use Vercel Functions
2. This endpoint will receive POST requests from the bridge server
3. Use WebSockets or polling to update the UI

In your React app, you can:

### 1. Fetch Emergencies
```javascript
const fetchEmergencies = async () => {
  const response = await fetch('http://localhost:3001/api/v1/emergencies');
  const data = await response.json();
  return data.data.emergencies;
};
```

### 2. Listen for Real-time Updates
```javascript
const eventSource = new EventSource('http://localhost:3001/api/emergencies/stream');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'new-emergency') {
    // Handle new emergency
    setEmergencies(prev => [...prev, data.data]);
  }
};
```

### 3. Acknowledge Emergency
```javascript
const acknowledgeEmergency = async (emergencyId) => {
  await fetch(`http://localhost:3001/api/v1/emergencies/${emergencyId}/acknowledge`, {
    method: 'POST'
  });
};
```

## Testing the Integration

1. **Start all servers** (Flask, Bridge, React)
2. **Go to Flask interface**: `http://localhost:5000`
3. **Start the system** and report an emergency
4. **Check React frontend**: Should receive the emergency data automatically
5. **Check bridge server logs**: Should show received dispatch reports

## Troubleshooting

### Flask can't connect to bridge server
- Make sure bridge server is running on port 3001
- Check firewall settings
- Verify the URL in `app.py` is correct

### React frontend not receiving data
- Check if bridge server is receiving dispatch reports
- Verify React app is listening on correct endpoints
- Check browser console for CORS errors

### Data format issues
- Verify the emergency data matches your React interface
- Check bridge server logs for data format errors
- Ensure all required fields are present

## Production Deployment

For production:
1. Use environment variables for URLs and ports
2. Implement proper authentication
3. Use HTTPS for all communications
4. Add proper error handling and logging
5. Consider using a message queue (Redis/RabbitMQ) for reliability
