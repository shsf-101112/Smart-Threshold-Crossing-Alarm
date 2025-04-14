/**
 * Dashboard JavaScript for the Smart Threshold Crossing Alarm system
 */

// Global WebSocket connection
let socket = null;
let reconnectInterval = null;
let soundEnabled = false;
let alarmSound = document.getElementById('alarm-sound');

// DOM Elements
const connectionStatus = document.getElementById('connection-status');
const startSimButton = document.getElementById('start-simulation');
const stopSimButton = document.getElementById('stop-simulation');
const triggerSpikeButton = document.getElementById('trigger-spike');
const spikeMetricSelect = document.getElementById('spike-metric');
const clearAlarmsButton = document.getElementById('clear-alarms');
const toggleSoundButton = document.getElementById('toggle-sound');
const updateThresholdsButton = document.getElementById('update-thresholds');
const resetThresholdsButton = document.getElementById('reset-thresholds');

// Metric display elements
const metricElements = {
    cpu: {
        value: document.getElementById('cpu-value'),
        bar: document.getElementById('cpu-bar'),
        container: document.getElementById('cpu-container')
    },
    memory: {
        value: document.getElementById('memory-value'),
        bar: document.getElementById('memory-bar'),
        container: document.getElementById('memory-container')
    },
    bandwidth: {
        value: document.getElementById('bandwidth-value'),
        bar: document.getElementById('bandwidth-bar'),
        container: document.getElementById('bandwidth-container')
    },
    latency: {
        value: document.getElementById('latency-value'),
        bar: document.getElementById('latency-bar'),
        container: document.getElementById('latency-container')
    }
};

// Threshold input elements
const thresholdInputs = {
    cpu: {
        warning: document.getElementById('cpu-warning'),
        critical: document.getElementById('cpu-critical')
    },
    memory: {
        warning: document.getElementById('memory-warning'),
        critical: document.getElementById('memory-critical')
    },
    bandwidth: {
        warning: document.getElementById('bandwidth-warning'),
        critical: document.getElementById('bandwidth-critical')
    },
    latency: {
        warning: document.getElementById('latency-warning'),
        critical: document.getElementById('latency-critical')
    }
};

// Alarm elements
const alarmStatus = document.getElementById('alarm-status');
const alarmHistory = document.getElementById('alarm-history');

/**
 * Connect to the WebSocket server
 */
function connectWebSocket() {
    // Close existing connection if any
    if (socket) {
        socket.close();
    }
    
    // Create WebSocket URL based on current location
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    socket = new WebSocket(wsUrl);
    
    // Connection opened
    // Fix get_config to use the expected action format:
socket.addEventListener('open', (event) => {
    console.log('Connected to server');
    connectionStatus.textContent = 'Connected';
    connectionStatus.classList.add('connected');
    
    // Clear any reconnect interval
    if (reconnectInterval) {
        clearInterval(reconnectInterval);
        reconnectInterval = null;
    }
    
    // Request current configuration
    socket.send(JSON.stringify({ action: 'get_thresholds' }));
});
    
    // Listen for messages
    socket.addEventListener('message', (event) => {
        try {
            const message = JSON.parse(event.data);
            handleMessage(message);
        } catch (error) {
            console.error('Error parsing message:', error);
        }
    });
    
    // Connection closed
    socket.addEventListener('close', (event) => {
        console.log('Disconnected from server');
        connectionStatus.textContent = 'Disconnected';
        connectionStatus.classList.remove('connected');
        
        // Set up reconnection
        if (!reconnectInterval) {
            reconnectInterval = setInterval(() => {
                console.log('Attempting to reconnect...');
                connectWebSocket();
            }, 5000);
        }
    });
    
    // Connection error
    socket.addEventListener('error', (event) => {
        console.error('WebSocket error:', event);
    });
}

/**
 * Send a message to the server
 */
function sendMessage(type, data) {
    if (socket && socket.readyState === WebSocket.OPEN) {
        const message = {
            type: type,
            ...data
        };
        socket.send(JSON.stringify(message));
    } else {
        console.warn('Cannot send message, socket is not connected');
    }
}

/**
 * Handle incoming messages from the server
 */
function handleMessage(message) {
    console.log("Received message:", message);
    
    // Handle metrics_update messages
    if (message.type === 'metrics_update') {
        updateMetrics(message.data);
        return;
    }
    
    // Handle alarm_update messages
    if (message.type === 'alarm_update') {
        updateAlarms(message.status, message.history);
        return;
    }
    
    // Handle status responses
    if (message.status) {
        console.log(`Received status: ${message.status}`);
        
        if (message.status === 'simulation_started') {
            startSimButton.disabled = true;
            stopSimButton.disabled = false;
        } else if (message.status === 'simulation_stopped') {
            startSimButton.disabled = false;
            stopSimButton.disabled = true;
        }
        
        return;
    }
    
    // Handle thresholds
    if (message.thresholds) {
        updateConfig({ thresholds: message.thresholds });
        return;
    }
    
    console.warn('Unknown message format:', message);
}

/**
 * Update metrics display
 */
function updateMetrics(metrics) {
    for (const [metric, data] of Object.entries(metrics)) {
        const elements = metricElements[metric];
        if (!elements) continue;
        
        // Format value based on metric type
        let displayValue;
        let percentage;
        
        switch (metric) {
            case 'cpu':
            case 'memory':
                displayValue = `${data.value.toFixed(1)}%`;
                percentage = data.value;
                break;
                
            case 'bandwidth':
                displayValue = `${data.value.toFixed(1)} Mbps`;
                percentage = (data.value / 1000) * 100; // 1000 Mbps max
                break;
                
            case 'latency':
                displayValue = `${data.value.toFixed(1)} ms`;
                percentage = (data.value / 500) * 100; // 500 ms max
                break;
                
            default:
                displayValue = data.value.toFixed(1);
                percentage = data.value;
        }
        
        // Update displayed value and bar
        if (elements.value) {
            elements.value.textContent = displayValue;
        }
        
        if (elements.bar) {
            elements.bar.style.width = `${percentage}%`;
        }
    }
}

/**
 * Update alarm displays
 */
function updateAlarms(status, history) {
    console.log("Updating alarms with:", status, history);
    
    // Update status classes on metric containers
    for (const [metric, alarmStatus] of Object.entries(status || {})) {
        const elements = metricElements[metric];
        if (!elements || !elements.container) continue;
        
        console.log(`Setting ${metric} to ${alarmStatus}`);
        
        // Remove existing status classes
        elements.container.classList.remove('normal', 'warning', 'critical');
        
        // Add current status class
        elements.container.classList.add(alarmStatus);
    }
    
    // Check highest severity alarm
    let highestSeverity = 'normal';
    let activeAlarms = [];
    
    for (const [metric, alarmStatus] of Object.entries(status || {})) {
        if (alarmStatus !== 'normal') {
            const metricName = metric.charAt(0).toUpperCase() + metric.slice(1);
            activeAlarms.push(`${metricName}: ${alarmStatus.toUpperCase()}`);
            
            if (alarmStatus === 'critical') {
                highestSeverity = 'critical';
            } else if (alarmStatus === 'warning' && highestSeverity !== 'critical') {
                highestSeverity = 'warning';
            }
        }
    }
    
    // Update alarm status display
    if (highestSeverity === 'normal') {
        alarmStatus.textContent = 'No Alarms';
        alarmStatus.className = 'no-alarm';
    } else {
        alarmStatus.textContent = activeAlarms.join(', ');
        alarmStatus.className = `${highestSeverity}-alarm`;
        
        // Play sound if enabled and critical alarm
        if (soundEnabled && highestSeverity === 'critical' && alarmSound) {
            alarmSound.play().catch(error => {
                console.error("Error playing alarm sound:", error);
            });
        }
    }
    
    // Update alarm history
    if (alarmHistory && history) {
        alarmHistory.innerHTML = '';
        
        if (history.length === 0) {
            const emptyItem = document.createElement('div');
            emptyItem.className = 'alarm-history-item';
            emptyItem.textContent = 'No alarm history';
            alarmHistory.appendChild(emptyItem);
        } else {
            history.forEach(entry => {
                const historyItem = document.createElement('div');
                historyItem.className = `alarm-history-item ${entry.status || 'normal'}`;
                
                const timestamp = document.createElement('span');
                timestamp.className = 'timestamp';
                timestamp.textContent = entry.timestamp || '';
                
                const message = document.createElement('div');
                message.textContent = entry.message || '';
                
                historyItem.appendChild(timestamp);
                historyItem.appendChild(message);
                
                alarmHistory.appendChild(historyItem);
            });
        }
    }
}

/**
 * Handle incoming messages from the server
 */
function handleMessage(message) {
    console.log("Received message:", message);
    
    // Handle metrics_update messages
    if (message.type === 'metrics_update') {
        updateMetrics(message.data);
        return;
    }
    
    // Handle alarm_update messages
    if (message.type === 'alarm_update') {
        updateAlarms(message.status, message.history);
        return;
    }
    
    // Handle status responses
    if (message.status) {
        console.log(`Received status: ${message.status}`);
        
        if (message.status === 'simulation_started') {
            startSimButton.disabled = true;
            stopSimButton.disabled = false;
        } else if (message.status === 'simulation_stopped') {
            startSimButton.disabled = false;
            stopSimButton.disabled = true;
        }
        
        return;
    }
    
    // Handle thresholds
    if (message.thresholds) {
        updateConfig({ thresholds: message.thresholds });
        return;
    }
    
    console.warn('Unknown message format:', message);
}

/**
 * Update configuration display
 */
function updateConfig(data) {
    const thresholds = data.thresholds || {};
    
    // Update threshold inputs
    for (const [metric, values] of Object.entries(thresholds)) {
        const inputs = thresholdInputs[metric];
        if (!inputs) continue;
        
        if (inputs.warning) {
            inputs.warning.value = values.warning;
        }
        
        if (inputs.critical) {
            inputs.critical.value = values.critical;
        }
    }
}

/**
 * Update simulation status
 */
function updateSimulationStatus(data) {
    const status = data.status;
    
    if (status === 'running') {
        startSimButton.disabled = true;
        stopSimButton.disabled = false;
    } else {
        startSimButton.disabled = false;
        stopSimButton.disabled = true;
    }
}

/**
 * Gather current threshold values
 */
function getThresholdValues() {
    const thresholds = {};
    
    for (const [metric, inputs] of Object.entries(thresholdInputs)) {
        const warning = parseFloat(inputs.warning.value);
        const critical = parseFloat(inputs.critical.value);
        
        if (!isNaN(warning) && !isNaN(critical)) {
            thresholds[metric] = {
                warning,
                critical
            };
        }
    }
    
    return thresholds;
}

// And fix the threshold update button:
updateThresholdsButton.addEventListener('click', () => {
    const thresholds = getThresholdValues();
    
    for (const [metric, values] of Object.entries(thresholds)) {
        socket.send(JSON.stringify({
            action: 'update_threshold',
            metric: metric,
            warning: values.warning,
            critical: values.critical
        }));
    }
});

/**
 * Initialize the dashboard
 */
function initDashboard() {
    // Connect to WebSocket
    connectWebSocket();
    
    // Set up event listeners
    // Fix for the start button:
// Start simulation button
startSimButton.addEventListener('click', () => {
    socket.send(JSON.stringify({ action: 'start_simulation' }));
});

// Stop simulation button
stopSimButton.addEventListener('click', () => {
    socket.send(JSON.stringify({ action: 'stop_simulation' }));
});

// Trigger spike button
triggerSpikeButton.addEventListener('click', () => {
    const metric = spikeMetricSelect.value;
    socket.send(JSON.stringify({ 
        action: 'trigger_spike',
        metric: metric
    }));
});

// Clear alarms button
clearAlarmsButton.addEventListener('click', () => {
    socket.send(JSON.stringify({ action: 'clear_alarms' }));
});
    
    toggleSoundButton.addEventListener('click', () => {
        soundEnabled = !soundEnabled;
        toggleSoundButton.textContent = soundEnabled ? 'Disable Sound' : 'Enable Sound';
        toggleSoundButton.classList.toggle('sound-disabled', !soundEnabled);
    });
    
    updateThresholdsButton.addEventListener('click', () => {
        const thresholds = getThresholdValues();
        
        for (const [metric, values] of Object.entries(thresholds)) {
            sendMessage('threshold_update', {
                metric,
                warning: values.warning,
                critical: values.critical
            });
        }
    });
    
    resetThresholdsButton.addEventListener('click', () => {
        // Request current configuration (will reset to defaults)
        sendMessage('get_config', {});
    });
    
    // Disable stop button initially
    stopSimButton.disabled = true;
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', initDashboard);