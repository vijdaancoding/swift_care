// Example React component for integrating with the emergency system
// Add this to your stratagem-react project

import React, { useState, useEffect } from 'react';

const EmergencyDashboard = () => {
  const [emergencies, setEmergencies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Bridge server URL - change this to your bridge server URL
  const BRIDGE_SERVER_URL = 'http://localhost:3001';

  useEffect(() => {
    const fetchEmergencies = async () => {
      try {
        const response = await fetch(`${BRIDGE_SERVER_URL}/api/v1/emergencies`);
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        setEmergencies(data.data.emergencies);
        setError(null);
      } catch (err) {
        console.error('Error fetching emergencies:', err);
        setError('Failed to fetch emergencies. Make sure the bridge server is running.');
      } finally {
        setLoading(false);
      }
    };

    // Fetch initially
    fetchEmergencies();
    
    // Poll every 5 seconds for new emergencies
    const interval = setInterval(fetchEmergencies, 5000);
    
    return () => clearInterval(interval);
  }, []);

  const acknowledgeEmergency = async (emergencyId) => {
    try {
      const response = await fetch(`${BRIDGE_SERVER_URL}/api/v1/emergencies/${emergencyId}/acknowledge`, {
        method: 'POST'
      });
      
      if (response.ok) {
        // Update local state
        setEmergencies(prev => 
          prev.map(emergency => 
            emergency.id === emergencyId 
              ? { ...emergency, status: 'responding', updatedAt: new Date().toISOString() }
              : emergency
          )
        );
      }
    } catch (err) {
      console.error('Error acknowledging emergency:', err);
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'Critical': return 'bg-red-500';
      case 'High': return 'bg-orange-500';
      case 'Medium': return 'bg-yellow-500';
      case 'Low': return 'bg-green-500';
      default: return 'bg-gray-500';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'bg-red-100 text-red-800';
      case 'responding': return 'bg-blue-100 text-blue-800';
      case 'resolved': return 'bg-green-100 text-green-800';
      case 'cancelled': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg">Loading emergencies...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
        <strong className="font-bold">Error:</strong>
        <span className="block sm:inline"> {error}</span>
      </div>
    );
  }

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">Emergency Dashboard</h1>
      
      {emergencies.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-gray-500 text-lg">No emergencies reported</div>
          <div className="text-gray-400 text-sm mt-2">
            Report emergencies through the Flask chat interface
          </div>
        </div>
      ) : (
        <div className="grid gap-4">
          {emergencies.map((emergency) => (
            <div key={emergency.id} className="bg-white border rounded-lg p-6 shadow-sm">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h2 className="text-xl font-semibold">{emergency.title}</h2>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium text-white ${getPriorityColor(emergency.priority)}`}>
                      {emergency.priority}
                    </span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(emergency.status)}`}>
                      {emergency.status}
                    </span>
                  </div>
                  <p className="text-gray-600 mb-2">{emergency.description}</p>
                  <div className="text-sm text-gray-500">
                    <div>📍 {emergency.address}</div>
                    <div>🕒 {new Date(emergency.timestamp).toLocaleString()}</div>
                    <div>👤 Reported by: {emergency.reportedBy.name}</div>
                    <div>📊 Severity: {emergency.severity}/10</div>
                  </div>
                </div>
                
                {emergency.status === 'active' && (
                  <button
                    onClick={() => acknowledgeEmergency(emergency.id)}
                    className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded text-sm font-medium"
                  >
                    Acknowledge
                  </button>
                )}
              </div>
              
              {emergency.assignedUnits && emergency.assignedUnits.length > 0 && (
                <div className="mt-4">
                  <h3 className="text-sm font-medium text-gray-700 mb-2">Assigned Units:</h3>
                  <div className="flex flex-wrap gap-2">
                    {emergency.assignedUnits.map((unit, index) => (
                      <span key={index} className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
                        {unit}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              
              {emergency.images && emergency.images.length > 0 && (
                <div className="mt-4">
                  <h3 className="text-sm font-medium text-gray-700 mb-2">Images:</h3>
                  <div className="flex gap-2">
                    {emergency.images.map((image, index) => (
                      <img 
                        key={index} 
                        src={image} 
                        alt={`Emergency ${emergency.id} - Image ${index + 1}`}
                        className="w-20 h-20 object-cover rounded"
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
      
      <div className="mt-6 text-center text-sm text-gray-500">
        <div>Bridge Server: {BRIDGE_SERVER_URL}</div>
        <div>Last updated: {new Date().toLocaleString()}</div>
      </div>
    </div>
  );
};

export default EmergencyDashboard;
