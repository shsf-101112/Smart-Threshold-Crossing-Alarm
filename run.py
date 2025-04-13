#!/usr/bin/env python
"""
Main entry point for the Smart Threshold Crossing Alarm application.
"""
import sys
from twisted.internet import reactor
from twisted.python import log

from threshold_alarm.web import create_web_server
from threshold_alarm.metrics import MetricsFactory
from threshold_alarm.alarm import AlarmManager
from threshold_alarm.threshold import ThresholdManager

def main():
    # Set up logging
    log.startLogging(sys.stdout)
    
    # Create core components
    threshold_manager = ThresholdManager()
    alarm_manager = AlarmManager(threshold_manager)
    metrics_factory = MetricsFactory(threshold_manager, alarm_manager)
    
    # Start the metrics simulation
    metrics_factory.start_simulation()
    
    # Create and start the web server (on port 8080)
    web_server = create_web_server(metrics_factory, threshold_manager, alarm_manager)
    
    # Start the Twisted reactor
    print("Starting Smart Threshold Crossing Alarm")
    print("Web interface available at http://localhost:8080")
    
    reactor.run()

if __name__ == "__main__":
    main()