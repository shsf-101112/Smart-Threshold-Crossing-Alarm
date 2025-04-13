"""
Threshold module for managing and checking metric thresholds.
"""
from twisted.python import log
from threshold_alarm.config import DEFAULT_THRESHOLDS

class ThresholdManager:
    """
    Manages thresholds for different metrics and checks if values exceed them.
    """
    def __init__(self):
        # Initialize with default thresholds
        self.thresholds = {}
        for metric, values in DEFAULT_THRESHOLDS.items():
            self.thresholds[metric] = {
                "warning": values["warning"],
                "critical": values["critical"]
            }
        
        log.msg(f"ThresholdManager initialized with defaults: {self.thresholds}")
    
    def check_threshold(self, metric, value):
        """
        Check if a metric value exceeds thresholds.
        
        Returns:
            str: 'normal', 'warning', or 'critical'
        """
        if metric not in self.thresholds:
            return 'normal'
        
        # Check critical first (higher priority)
        if value >= self.thresholds[metric]["critical"]:
            return 'critical'
        elif value >= self.thresholds[metric]["warning"]:
            return 'warning'
        else:
            return 'normal'
    
    def update_threshold(self, metric, warning, critical):
        """
        Update threshold values for a specific metric.
        
        Args:
            metric (str): Name of the metric
            warning (float): Warning threshold value
            critical (float): Critical threshold value
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not metric:
            return False
        
        # Validate threshold values
        try:
            warning_val = float(warning)
            critical_val = float(critical)
            
            # Critical should be higher than warning
            if critical_val <= warning_val:
                log.err(f"Invalid thresholds: Critical ({critical_val}) must be greater than Warning ({warning_val})")
                return False
                
            # Update thresholds
            self.thresholds[metric] = {
                "warning": warning_val,
                "critical": critical_val
            }
            
            log.msg(f"Updated thresholds for {metric}: warning={warning_val}, critical={critical_val}")
            return True
            
        except (ValueError, TypeError) as e:
            log.err(f"Invalid threshold values: {e}")
            return False
    
    def get_threshold(self, metric):
        """
        Get the threshold values for a specific metric.
        
        Args:
            metric (str): Name of the metric
            
        Returns:
            dict: Threshold values or None if metric doesn't exist
        """
        return self.thresholds.get(metric)
    
    def get_all_thresholds(self):
        """
        Get all current threshold values.
        
        Returns:
            dict: All threshold values
        """
        return self.thresholds
    
    def reset_to_defaults(self):
        """
        Reset all thresholds to default values.
        
        Returns:
            bool: True if successful
        """
        self.thresholds = {}
        for metric, values in DEFAULT_THRESHOLDS.items():
            self.thresholds[metric] = {
                "warning": values["warning"],
                "critical": values["critical"]
            }
        
        log.msg("Thresholds reset to defaults")
        return True