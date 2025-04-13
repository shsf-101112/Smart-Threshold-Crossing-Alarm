"""
Alarm module for managing and triggering alarms based on threshold crossings.
"""
from datetime import datetime
from twisted.python import log

from threshold_alarm.config import MAX_ALARM_HISTORY

class AlarmManager:
    """
    Manages alarms triggered by threshold crossings.
    """
    def __init__(self, threshold_manager):
        self.threshold_manager = threshold_manager
        self.alarms = {}
        self.alarm_history = []
        self.subscribers = set()
        
        # Initialize alarm state for all metrics
        for metric in threshold_manager.thresholds.keys():
            self.alarms[metric] = {
                "status": "normal",
                "last_triggered": None,
                "value": 0,
                "unit": ""
            }
        
        log.msg("AlarmManager initialized")
    
    def update_alarm(self, metric, value, status, unit=None):
        """
        Update alarm status for a metric.
        
        Args:
            metric (str): Name of the metric
            value (float): Current value
            status (str): 'normal', 'warning', or 'critical'
            unit (str, optional): Unit of measurement
        """
        if metric not in self.alarms:
            # Initialize new metric alarm
            self.alarms[metric] = {
                "status": "normal",
                "last_triggered": None,
                "value": 0,
                "unit": unit or ""
            }
        
        # Get the current unit if not provided
        if not unit and "unit" in self.alarms[metric]:
            unit = self.alarms[metric]["unit"]
        
        # Check if status has changed
        old_status = self.alarms[metric]["status"]
        if old_status != status:
            now = datetime.now()
            
            # Update alarm state
            self.alarms[metric]["status"] = status
            self.alarms[metric]["value"] = value
            self.alarms[metric]["unit"] = unit or ""
            
            if status != "normal":
                # Record alarm trigger time
                self.alarms[metric]["last_triggered"] = now
                
                # Add to alarm history
                history_entry = {
                    "metric": metric,
                    "status": status,
                    "value": value,
                    "unit": unit or "",
                    "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "message": f"{metric.upper()} {status}: {value}{unit or ''}"
                }
                
                self.alarm_history.insert(0, history_entry)
                
                # Limit history size
                if len(self.alarm_history) > MAX_ALARM_HISTORY:
                    self.alarm_history = self.alarm_history[:MAX_ALARM_HISTORY]
                
                log.msg(f"Alarm triggered: {history_entry['message']}")
            else:
                log.msg(f"Alarm cleared for {metric}")
            
            # Notify subscribers about alarm change
            self.notify_subscribers()
    
    def get_alarm_status(self, metric=None):
        """
        Get the current alarm status.
        
        Args:
            metric (str, optional): Name of the metric
            
        Returns:
            dict: Status information for the requested metric or all metrics
        """
        if metric:
            return self.alarms.get(metric, {"status": "normal"})
        
        # Return all alarms
        return self.alarms
    
    def get_highest_severity(self):
        """
        Get the highest severity alarm currently active.
        
        Returns:
            str: 'normal', 'warning', or 'critical'
        """
        has_warning = False
        
        for alarm in self.alarms.values():
            if alarm["status"] == "critical":
                return "critical"
            elif alarm["status"] == "warning":
                has_warning = True
        
        return "warning" if has_warning else "normal"
    
    def get_alarm_history(self):
        """
        Get the alarm history.
        
        Returns:
            list: Alarm history entries
        """
        return self.alarm_history
    
    def clear_alarms(self):
        """
        Clear all active alarms.
        
        Returns:
            bool: True if successful
        """
        for metric in self.alarms:
            self.alarms[metric]["status"] = "normal"
            self.alarms[metric]["last_triggered"] = None
        
        log.msg("All alarms cleared")
        self.notify_subscribers()
        return True
    
    def add_subscriber(self, subscriber):
        """Add a subscriber for alarm updates."""
        self.subscribers.add(subscriber)
        # Immediately send current status
        subscriber.send_alarm_update(self.get_alarm_status(), self.get_alarm_history())
    
    def remove_subscriber(self, subscriber):
        """Remove a subscriber."""
        if subscriber in self.subscribers:
            self.subscribers.remove(subscriber)
    
    def notify_subscribers(self):
        """Send alarm updates to all subscribers."""
        alarm_status = self.get_alarm_status()
        alarm_history = self.get_alarm_history()
        
        for subscriber in list(self.subscribers):
            try:
                subscriber.send_alarm_update(alarm_status, alarm_history)
            except Exception as e:
                log.err(f"Error sending alarm update to subscriber: {e}")
                self.remove_subscriber(subscriber)