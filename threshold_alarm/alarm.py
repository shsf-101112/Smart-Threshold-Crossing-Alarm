"""
Alarm module for managing and triggering alarms based on threshold crossings.
"""
from datetime import datetime
from twisted.python import log
from threshold_alarm.config import MAX_ALARM_HISTORY
from threshold_alarm.protocol import MetricsProtocol

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
            self.alarms[metric] = {
                "status": "normal",
                "last_triggered": None,
                "value": 0,
                "unit": unit or ""
            }

        if not unit:
            unit = self.alarms[metric].get("unit", "")

        old_status = self.alarms[metric]["status"]
        if old_status != status:
            now_str = datetime.now().isoformat()

            # Update alarm
            self.alarms[metric].update({
                "status": status,
                "value": value,
                "unit": unit
            })

            if status != "normal":
                self.alarms[metric]["last_triggered"] = now_str

                history_entry = {
                    "metric": metric,
                    "status": status,
                    "value": value,
                    "unit": unit,
                    "timestamp": now_str,
                    "message": f"{metric.upper()} {status}: {value}{unit}"
                }

                self.alarm_history.insert(0, history_entry)
                self.alarm_history = self.alarm_history[:MAX_ALARM_HISTORY]

                log.msg(f"Alarm triggered: {history_entry['message']}")
            else:
                log.msg(f"Alarm cleared for {metric}")

            self.notify_subscribers()

    def get_alarm_status(self, metric=None):
        """
        Get the current alarm status.

        Args:
            metric (str, optional): Name of the metric

        Returns:
            dict: Status for one or all metrics
        """
        if metric:
            return self.alarms.get(metric, {"status": "normal"})
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
        """Returns the alarm history."""
        return self.alarm_history

    def clear_alarms(self):
        """Clears all current alarms and notifies subscribers."""
        for metric in self.alarms:
            self.alarms[metric]["status"] = "normal"
            self.alarms[metric]["last_triggered"] = None

        log.msg("All alarms cleared")
        self.notify_subscribers()
        return True

    def add_subscriber(self, subscriber: MetricsProtocol):
        """Add a subscriber for alarm updates."""
        self.subscribers.add(subscriber)
        try:
            subscriber.send_alarm_update(self.get_alarm_status(), self.get_alarm_history())
        except Exception as e:
            log.err(f"Error sending initial alarm update to subscriber: {e}")
            self.remove_subscriber(subscriber)

    def remove_subscriber(self, subscriber):
        """Unregisters a subscriber."""
        self.subscribers.discard(subscriber)

    def notify_subscribers(self):
        """Notify all subscribers of alarm updates."""
        for subscriber in self.subscribers:
            if hasattr(subscriber, 'send_alarm_update'):
                subscriber.send_alarm_update(self.get_alarm_status(), self.alarm_history)

