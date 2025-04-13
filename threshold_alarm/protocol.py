"""
WebSocket protocol for communicating with web clients.
"""
import json
from twisted.python import log
from autobahn.twisted.websocket import WebSocketServerProtocol

class MetricsProtocol(WebSocketServerProtocol):
    """WebSocket protocol for streaming metrics and alarm data."""
    
    def onConnect(self, request):
        """Handle new WebSocket connection."""
        log.msg(f"Client connecting: {request.peer}")
    
    def onOpen(self):
        """Handle WebSocket connection opened."""
        log.msg(f"WebSocket connection open")
        
        # Register this connection with metrics and alarm factories
        factory = self.factory
        factory.register_connection(self)
    
    def onClose(self, wasClean, code, reason):
        """Handle WebSocket connection closed."""
        log.msg(f"WebSocket connection closed: {reason}")
        
        # Unregister from factories
        factory = self.factory
        factory.unregister_connection(self)
    
    def onMessage(self, payload, isBinary):
        """Handle message received from client."""
        if isBinary:
            log.msg("Binary message received and ignored")
            return
        
        try:
            # Decode and parse the JSON message
            message = json.loads(payload.decode('utf8'))
            message_type = message.get('type')
            
            if message_type == 'threshold_update':
                # Handle threshold update request
                metric = message.get('metric')
                warning = message.get('warning')
                critical = message.get('critical')
                
                if metric and warning is not None and critical is not None:
                    success = self.factory.threshold_manager.update_threshold(metric, warning, critical)
                    self.send_response('threshold_update', {'success': success})
            
            elif message_type == 'clear_alarms':
                # Handle alarm clear request
                success = self.factory.alarm_manager.clear_alarms()
                self.send_response('clear_alarms', {'success': success})
            
            elif message_type == 'simulation_control':
                # Handle simulation start/stop
                action = message.get('action')
                if action == 'start':
                    self.factory.metrics_factory.start_simulation()
                    self.send_response('simulation_control', {'status': 'running'})
                elif action == 'stop':
                    self.factory.metrics_factory.stop_simulation()
                    self.send_response('simulation_control', {'status': 'stopped'})
            
            elif message_type == 'simulate_spike':
                # Handle spike simulation request
                metric = message.get('metric')
                percentage = message.get('percentage', 0.9)
                
                if metric:
                    success = self.factory.metrics_factory.simulate_spike(metric, percentage)
                    self.send_response('simulate_spike', {'success': success})
            
            elif message_type == 'get_config':
                # Return current configuration
                thresholds = self.factory.threshold_manager.get_all_thresholds()
                self.send_response('config', {'thresholds': thresholds})
            
            else:
                log.msg(f"Unknown message type: {message_type}")
                self.send_response('error', {'message': 'Unknown command'})
                
        except json.JSONDecodeError:
            log.err("Invalid JSON received")
            self.send_response('error', {'message': 'Invalid JSON'})
        except Exception as e:
            log.err(f"Error processing message: {str(e)}")
            self.send_response('error', {'message': str(e)})
    
    def send_metrics(self, metrics):
        """Send metrics update to the client."""
        self.send_message('metrics_update', metrics)
    
    def send_alarm_update(self, alarms, history):
        """Send alarm update to the client."""
        self.send_message('alarm_update', {
            'alarms': alarms,
            'history': history
        })
    
    def send_response(self, response_type, data):
        """Send a response message to the client."""
        self.send_message(response_type, data)
    
    def send_message(self, message_type, data):
        """Send a message to the client."""
        message = {
            'type': message_type,
            'data': data
        }
        
        try:
            payload = json.dumps(message).encode('utf8')
            self.sendMessage(payload)
        except Exception as e:
            log.err(f"Error sending message to client: {e}")


class MetricsFactory:
    """
    Factory for the WebSocket protocol that manages connections and routes messages.
    """
    protocol = MetricsProtocol
    
    def __init__(self, metrics_factory, threshold_manager, alarm_manager):
        self.metrics_factory = metrics_factory
        self.threshold_manager = threshold_manager
        self.alarm_manager = alarm_manager
        self.connections = set()
    
    def register_connection(self, connection):
        """Register a new WebSocket connection."""
        self.connections.add(connection)
        
        # Subscribe the connection to metrics and alarms
        self.metrics_factory.add_subscriber(connection)
        self.alarm_manager.add_subscriber(connection)
    
    def unregister_connection(self, connection):
        """Unregister a WebSocket connection."""
        if connection in self.connections:
            self.connections.remove(connection)
            
            # Unsubscribe from metrics and alarms
            self.metrics_factory.remove_subscriber(connection)
            self.alarm_manager.remove_subscriber(connection)
    
    def broadcast(self, message_type, data):
        """Broadcast a message to all connections."""
        for connection in list(self.connections):
            try:
                connection.send_message(message_type, data)
            except Exception as e:
                log.err(f"Error broadcasting to connection: {e}")
                self.unregister_connection(connection)