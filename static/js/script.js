document.addEventListener('DOMContentLoaded', () => {
    // Establish a connection to the server
    const socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

    // Get references to all the dynamic UI elements
    const statusLight = document.getElementById('status-light');
    const statusText = document.getElementById('status-text');
    const agentFlow = document.getElementById('agent-flow');
    const conversationLog = document.getElementById('conversation-log');
    const dispatchReport = document.getElementById('dispatch-report');
    const meshNodes = {
        'V-Node': document.getElementById('v-node'),
        'Relay-Node': document.getElementById('relay-node'),
        'C-Node': document.getElementById('c-node')
    };

    let isDispatchSectionActive = false;

    // --- SOCKET.IO EVENT HANDLERS ---

    socket.on('connect', () => {
        statusLight.className = 'status-connected';
        statusText.textContent = 'Connected';
        console.log('Successfully connected to the server.');
        // Emit orchestrator connect event to start the agent system
        socket.emit('orchestrator_connect');
    });

    socket.on('disconnect', () => {
        statusLight.className = 'status-disconnected';
        statusText.textContent = 'Disconnected';
        console.error('Disconnected from the server.');
    });

    socket.on('status', (msg) => {
        console.log('Status update:', msg.data);
    });

    socket.on('new_output', (msg) => {
        const line = msg.data.trim();

        // Check for end-of-session signal first
        if (line === "---END_OF_SESSION---") {
            statusLight.className = 'status-completed';
            statusText.textContent = 'Session Completed';
            return; // Stop processing further
        }
        
        // Update status to 'running' on first real message
        if (statusLight.className !== 'status-running' && statusLight.className !== 'status-completed') {
            statusLight.className = 'status-running';
            statusText.textContent = 'Orchestration in Progress...';
        }

        // Parse and display the incoming line
        parseAndDisplay(line);
    });
    
    // --- UI UPDATE FUNCTIONS ---

    /**
     * Parses a log line and routes it to the correct display function.
     * @param {string} line - The log line from the backend.
     */
    function parseAndDisplay(line) {
        // Dispatch Report: This has high priority to capture multi-line reports
        if (line.startsWith('DISPATCH REPORT:')) {
            isDispatchSectionActive = true;
            dispatchReport.innerHTML = ''; // Clear placeholder
            addDispatchEntry(line);
            return;
        }
        if (isDispatchSectionActive && line.startsWith('=')) {
            isDispatchSectionActive = false; // End of dispatch report
        }
        if (isDispatchSectionActive) {
            addDispatchEntry(line);
            return;
        }

        // User and Agent conversation
        if (line.startsWith('You:')) {
            addLogEntry(line.substring(4).trim(), 'user');
        } else if (line.match(/^(Routing|Medical|Crime|Disaster|Allocator) Agent:/)) {
            addLogEntry(line.split(':')[1].trim(), 'agent');
        }
        // Agent Flow and transitions
        else if (line.startsWith('🔄 Current Agent:')) {
            const agentName = line.split(':')[1].trim();
            updateAgentFlow(agentName);
            addLogEntry(line, 'system');
        } 
        // Mesh Network simulation
        else if (line.startsWith('[V-Node]')) {
           animateNode('V-Node');
           addLogEntry(line, 'system');
        } else if (line.startsWith('[Relay-Node]')) {
           animateNode('Relay-Node');
           addLogEntry(line, 'system');
        } else if (line.startsWith('[C-Node]')) {
           animateNode('C-Node');
           addLogEntry(line, 'system');
        }
        // General system messages that should be visible
        else if (line.startsWith('✅') || line.startsWith('Forwarding') || line.startsWith('📊 SESSION SUMMARY')) {
             addLogEntry(line, 'system');
        }
        // Hide purely structural or repetitive logs from the main view to reduce clutter
        else if (line.startsWith('='*10) || line.startsWith('---') || line.trim() === '') {
            // Do nothing, hide these lines
        }
        // Default catch-all for other system messages
        else {
            // You can uncomment the line below to see ALL logs, even filtered ones
            // addLogEntry(line, 'system');
        }
    }

    /**
     * Adds a new entry to the conversation log.
     * @param {string} text - The message text.
     * @param {string} type - 'user', 'agent', or 'system'.
     */
    function addLogEntry(text, type) {
        const entry = document.createElement('div');
        entry.className = `log-entry log-${type}`;
        entry.textContent = text;
        conversationLog.appendChild(entry);
        // Auto-scroll to the bottom
        conversationLog.scrollTop = conversationLog.scrollHeight;
    }

    /**
     * Updates the agent flow visualization at the top of the page.
     * @param {string} agentName - The name of the new active agent.
     */
    function updateAgentFlow(agentName) {
        if (agentFlow.innerHTML !== '' && !agentFlow.innerHTML.endsWith('</div>')) {
            const arrow = document.createElement('div');
            arrow.className = 'flow-arrow';
            arrow.textContent = '➔';
            agentFlow.appendChild(arrow);
        }
        
        // Deactivate previous agent boxes
        const existingBoxes = agentFlow.querySelectorAll('.agent-box');
        existingBoxes.forEach(box => box.classList.remove('active'));

        const agentDiv = document.createElement('div');
        agentDiv.className = 'agent-box active';
        agentDiv.textContent = agentName;
        agentFlow.appendChild(agentDiv);
    }
    
    /**
     * Briefly highlights a mesh network node to simulate activity.
     * @param {string} nodeName - The key of the node in the meshNodes object.
     */
    function animateNode(nodeName) {
        const node = meshNodes[nodeName];
        if (node) {
            node.classList.add('active');
            setTimeout(() => {
                node.classList.remove('active');
            }, 1200); // Animation duration
        }
    }

    /**
     * Adds a line to the final dispatch report card.
     * @param {string} text - The line of text for the report.
     */
    function addDispatchEntry(text) {
        // Append text, preserving line breaks
        dispatchReport.textContent += text + '\n';
    }
});