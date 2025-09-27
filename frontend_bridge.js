// Simple Express.js server to bridge Flask backend with React frontend
const express = require('express');
const cors = require('cors');
const axios = require('axios');
const app = express();
const port = 3001; // Different port from React dev server

// Middleware
app.use(cors());
app.use(express.json());

// Store received emergencies
let emergencies = [];

// Function to send emergency data to deployed React app
async function sendToDeployedReactApp(emergencyData) {
    try {
        const deployedReactUrl = 'https://stratagem-react.vercel.app';
        
        // Try to send to deployed React app's API endpoint
        // Note: You'll need to create an API route in your React app to receive this
        const response = await axios.post(`${deployedReactUrl}/api/emergencies/receive`, emergencyData, {
            headers: {
                'Content-Type': 'application/json'
            },
            timeout: 5000
        });
        
        console.log('Successfully sent emergency to deployed React app:', response.status);
    } catch (error) {
        console.log('Could not send to deployed React app (this is normal if no API route exists):', error.message);
        // This is expected if the React app doesn't have an API route to receive emergencies
        // The emergency data is still stored locally and available via the API endpoints
    }
}

// Endpoint to receive dispatch reports from Flask backend
app.post('/api/emergencies/receive-dispatch', async (req, res) => {
    try {
        const emergencyData = req.body;
        console.log('Received dispatch report:', emergencyData);
        
        // Extract the emergency from the data
        if (emergencyData.success && emergencyData.data && emergencyData.data.emergencies) {
            const emergency = emergencyData.data.emergencies[0];
            emergencies.push(emergency);
            
            console.log('Emergency added:', emergency.id);
            
            // Broadcast to all connected clients via Server-Sent Events
            broadcastEmergency(emergency);
            
            // Also send to deployed React app on Vercel
            await sendToDeployedReactApp(emergencyData);
            
            res.status(200).json({ 
                success: true, 
                message: 'Emergency received and forwarded successfully',
                emergencyId: emergency.id 
            });
        } else {
            res.status(400).json({ 
                success: false, 
                message: 'Invalid emergency data format' 
            });
        }
    } catch (error) {
        console.error('Error processing dispatch:', error);
        res.status(500).json({ 
            success: false, 
            message: 'Internal server error' 
        });
    }
});

// Endpoint for React frontend to fetch emergencies
app.get('/api/v1/emergencies', (req, res) => {
    res.json({
        success: true,
        data: {
            emergencies: emergencies
        }
    });
});

// Endpoint to acknowledge emergency
app.post('/api/v1/emergencies/:id/acknowledge', (req, res) => {
    const emergencyId = parseInt(req.params.id);
    const emergency = emergencies.find(e => e.id === emergencyId);
    
    if (emergency) {
        emergency.status = 'responding';
        emergency.updatedAt = new Date().toISOString();
        
        res.json({
            success: true,
            message: 'Emergency acknowledged'
        });
    } else {
        res.status(404).json({
            success: false,
            message: 'Emergency not found'
        });
    }
});

// Server-Sent Events for real-time updates
const clients = new Set();

app.get('/api/emergencies/stream', (req, res) => {
    res.writeHead(200, {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Access-Control-Allow-Origin': '*'
    });

    const clientId = Date.now();
    clients.add({ id: clientId, response: res });

    req.on('close', () => {
        clients.delete({ id: clientId, response: res });
    });

    // Send initial data
    res.write(`data: ${JSON.stringify({ type: 'connected', clientId })}\n\n`);
});

function broadcastEmergency(emergency) {
    const message = JSON.stringify({
        type: 'new-emergency',
        data: emergency
    });

    clients.forEach(client => {
        try {
            client.response.write(`data: ${message}\n\n`);
        } catch (error) {
            console.error('Error broadcasting to client:', error);
            clients.delete(client);
        }
    });
}

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ 
        status: 'healthy', 
        timestamp: new Date().toISOString(),
        emergencyCount: emergencies.length 
    });
});

app.listen(port, () => {
    console.log(`Frontend bridge server running on http://localhost:${port}`);
    console.log(`Ready to receive dispatch reports from Flask backend`);
});

module.exports = app;
