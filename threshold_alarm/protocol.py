"""
WebSocket protocol for the threshold alarm application.
"""
from autobahn.twisted.websocket import WebSocketServerProtocol
from twisted.python import log
import json

class MetricsProtocol(WebSocketServerProtocol):
    """
    WebSocket protocol for handling metrics and alarm communication.
    """
    def onConnect(self, request):
        log.msg(f"Client connecting: {request.peer}")
    
    def onOpen(self):
        log.msg("WebSocket connection open")
        
        # Register this connection as a subscriber
        self.factory.metrics_factory.add_subscriber(self)
        self.factory.alarm_manager.add_subscriber(self)
    
    def onClose(self, wasClean, code, reason):
        log.msg(f"WebSocket connection closed: {reason}")
        
        # Remove from subscribers
        self.factory.metrics_factory.remove_subscriber(self)
        self.factory.alarm_manager.remove_subscriber(self)
    
    def onMessage(self, payload, isBinary):
        if isBinary:
            return
        
        try:
            # Parse the message
            message = json.loads(payload.decode('utf8'))
            action = message.get('action')
            
            log.msg(f"Received action: {action}")
            
            if action == 'start_simulation':  # THIS NEEDS TO MATCH WHAT YOUR JS SENDS
                # Start the metrics simulation
                self.factory.metrics_factory.start_simulation()
                self.sendMessage(json.dumps({"status": "simulation_started"}).encode('utf8'))
                log.msg("Simulation started via WebSocket")
                
            elif action == 'stop_simulation':
                # Stop the metrics simulation
                self.factory.metrics_factory.stop_simulation()
                self.sendMessage(json.dumps({"status": "simulation_stopped"}).encode('utf8'))
                log.msg("Simulation stopped via WebSocket")
                
            elif action == 'clear_alarms':
                # Clear all alarms
                self.factory.alarm_manager.clear_alarms()
                self.sendMessage(json.dumps({"status": "alarms_cleared"}).encode('utf8'))
                
            elif action == 'update_threshold':
                # Update threshold values
                result = self.factory.threshold_manager.update_threshold(
                    message.get('metric'),
                    message.get('warning'),
                    message.get('critical')
                )
                self.sendMessage(json.dumps({"status": "threshold_updated" if result else "threshold_error"}).encode('utf8'))
                
            elif action == 'trigger_spike':
                # Trigger a metric spike for testing
                metric = message.get('metric')
                if metric:
                    self.factory.metrics_factory.simulate_spike(metric)
                    self.sendMessage(json.dumps({"status": "spike_triggered"}).encode('utf8'))
                
            elif action == 'get_thresholds':
                # Send current thresholds
                thresholds = self.factory.threshold_manager.get_all_thresholds()
                self.sendMessage(json.dumps({"thresholds": thresholds}).encode('utf8'))
                
            else:
                log.msg(f"Unknown action: {action}")
                
        except json.JSONDecodeError:
            log.err("Invalid JSON message received")
        except Exception as e:
            log.err(f"Error processing message: {e}")
    
    def send_metrics(self, metrics):
        """Send metrics data to the connected client."""
        try:
            data = {
                'type': 'metrics_update',
                'data': metrics
            }
            metrics_json = json.dumps(data)
            self.sendMessage(metrics_json.encode('utf8'))
        except Exception as e:
            print(f"Error sending metrics: {e}")
    def send_alarm_update(self, status, history):
        """Send alarm status and history updates to the connected client."""
        try:
            data = {
                'type': 'alarm_update',
                'status': status,
                'history': history
            }
            alarm_json = json.dumps(data)
            self.sendMessage(alarm_json.encode('utf8'))
        except Exception as e:
            print(f"Error sending alarm update: {e}")
