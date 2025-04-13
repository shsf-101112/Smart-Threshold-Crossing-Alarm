"""
Web server module for the threshold alarm application.
"""
import os
from twisted.web.server import Site
from twisted.web.static import File
from twisted.internet import reactor
from twisted.web.resource import Resource
from twisted.python import log
from autobahn.twisted.websocket import WebSocketServerFactory
from autobahn.twisted.resource import WebSocketResource

from threshold_alarm.protocol import MetricsProtocol, MetricsFactory
from threshold_alarm.config import WEB_PORT, WEB_INTERFACE

class RootResource(Resource):
    """
    Root web resource that serves static files and WebSocket endpoint.
    """
    def __init__(self, ws_resource):
        Resource.__init__(self)
        self.ws_resource = ws_resource
        
        # Get the directory where static files are located
        current_dir = os.path.dirname(os.path.abspath(__file__))
        static_dir = os.path.join(os.path.dirname(current_dir), 'static')
        
        # Check if the static directory exists, create it if not
        if not os.path.exists(static_dir):
            os.makedirs(static_dir)
            log.msg(f"Created static directory: {static_dir}")
        
        # Create static file server
        self.static = File(static_dir)
    
    def getChild(self, name, request):
        """
        Route requests to appropriate handlers.
        """
        if name == b'ws':
            return self.ws_resource
        
        return self.static.getChild(name, request)

def create_web_server(metrics_factory, threshold_manager, alarm_manager):
    """
    Create and start the web server.
    
    Args:
        metrics_factory: Factory for generating metrics
        threshold_manager: Manager for handling thresholds
        alarm_manager: Manager for handling alarms
        
    Returns:
        The web server instance
    """
    # Create WebSocket factory
    factory = WebSocketServerFactory(f"ws://{WEB_INTERFACE}:{WEB_PORT}")
    factory.protocol = MetricsProtocol
    
    # Set up the metrics factory for the WebSocket protocol
    factory.metrics_factory = metrics_factory
    factory.threshold_manager = threshold_manager
    factory.alarm_manager = alarm_manager
    
    # Create WebSocket resource
    ws_resource = WebSocketResource(factory)
    
    # Create root resource
    root = RootResource(ws_resource)
    
    # Create and start web server
    site = Site(root)
    web_server = reactor.listenTCP(WEB_PORT, site, interface=WEB_INTERFACE)
    
    log.msg(f"Web server started on http://{WEB_INTERFACE}:{WEB_PORT}")
    
    return web_server