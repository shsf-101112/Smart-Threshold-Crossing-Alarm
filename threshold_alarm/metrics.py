"""
Metrics module for simulating network and system metrics.
"""
import random
from twisted.internet import task
from twisted.internet import reactor
from twisted.python import log

from threshold_alarm.config import SIMULATION_INTERVAL, METRIC_SPECS

class MetricsFactory:
    """
    Factory class that handles metric simulation and distribution.
    """
    def __init__(self, threshold_manager, alarm_manager):
        self.threshold_manager = threshold_manager
        self.alarm_manager = alarm_manager
        self.metrics = {}
        self.subscribers = set()
        self.simulation_loop = None
        self.is_simulating = False
        
        # Initialize metrics with default values
        for metric_name, spec in METRIC_SPECS.items():
            self.metrics[metric_name] = {
                "value": 0,
                "min": spec["min"],
                "max": spec["max"],
                "unit": spec["unit"],
                "volatility": spec["volatility"],
                "trend": 1,  # 1 for up, -1 for down
            }
    
    def start_simulation(self):
        """Start the metric simulation."""
        if self.is_simulating:
            return
        
        self.is_simulating = True
        self.simulation_loop = task.LoopingCall(self.simulate_metrics)
        self.simulation_loop.start(SIMULATION_INTERVAL)
        log.msg("Metric simulation started")
    
    def stop_simulation(self):
        """Stop the metric simulation."""
        if not self.is_simulating or not self.simulation_loop:
            return
        
        self.simulation_loop.stop()
        self.is_simulating = False
        log.msg("Metric simulation stopped")
    
    def simulate_metrics(self):
        """Generate simulated metric values."""
        updates = {}
        
        for metric_name, metric_data in self.metrics.items():
            # Possibly change trend direction (20% chance)
            if random.random() < 0.2:
                metric_data["trend"] = 1 if random.random() > 0.5 else -1
            
            # Calculate new value based on trend and volatility
            change = random.random() * metric_data["volatility"] * metric_data["trend"]
            new_value = metric_data["value"] + change
            
            # Ensure value stays within bounds
            new_value = max(metric_data["min"], min(metric_data["max"], new_value))
            
            # Update the metric value
            metric_data["value"] = new_value
            
            # Check if this metric exceeds threshold
            self.check_threshold(metric_name, new_value)
            
            # Add to updates
            updates[metric_name] = {
                "value": new_value,
                "unit": metric_data["unit"]
            }
        
        # Notify subscribers
        self.notify_subscribers(updates)
    
    def check_threshold(self, metric_name, value):
        """Check if a metric has crossed any thresholds."""
        status = self.threshold_manager.check_threshold(metric_name, value)
        self.alarm_manager.update_alarm(metric_name, value, status)
    
    def get_metric(self, metric_name):
        """Get the current value of a specific metric."""
        if metric_name in self.metrics:
            return {
                "value": self.metrics[metric_name]["value"],
                "unit": self.metrics[metric_name]["unit"]
            }
        return None
    
    def get_all_metrics(self):
        """Get all current metric values."""
        return {
            name: {
                "value": data["value"], 
                "unit": data["unit"]
            } for name, data in self.metrics.items()
        }
    
    def add_subscriber(self, subscriber):
        """Add a new subscriber for metric updates."""
        self.subscribers.add(subscriber)
        # Send current values immediately to new subscriber
        subscriber.send_metrics(self.get_all_metrics())
    
    def remove_subscriber(self, subscriber):
        """Remove a subscriber."""
        if subscriber in self.subscribers:
            self.subscribers.remove(subscriber)
    
    def notify_subscribers(self, metrics_update):
        """Send metric updates to all subscribers."""
        for subscriber in list(self.subscribers):
            try:
                subscriber.send_metrics(metrics_update)
            except Exception as e:
                log.err(f"Error sending metrics to subscriber: {e}")
                self.remove_subscriber(subscriber)

    def simulate_spike(self, metric_name, percentage=0.9):
        """Simulate a spike in a specific metric."""
        if metric_name not in self.metrics:
            return False
        
        # Calculate spike value (percentage of max)
        spike_value = self.metrics[metric_name]["max"] * percentage
        self.metrics[metric_name]["value"] = spike_value
        
        # Check threshold and update
        self.check_threshold(metric_name, spike_value)
        
        # Notify subscribers of this specific update
        update = {
            metric_name: {
                "value": spike_value,
                "unit": self.metrics[metric_name]["unit"]
            }
        }
        self.notify_subscribers(update)
        
        return True