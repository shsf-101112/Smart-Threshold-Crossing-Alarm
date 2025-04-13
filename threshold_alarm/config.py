"""
Configuration settings for the threshold alarm system.
"""

# Web server configuration
WEB_PORT = 8080
WEB_INTERFACE = "0.0.0.0"  # Listen on all interfaces

# Default thresholds
DEFAULT_THRESHOLDS = {
    "cpu": {
        "warning": 70,
        "critical": 90
    },
    "memory": {
        "warning": 65,
        "critical": 85
    },
    "bandwidth": {
        "warning": 700,
        "critical": 900
    },
    "latency": {
        "warning": 80,
        "critical": 150
    }
}

# Metric simulation settings
SIMULATION_INTERVAL = 1.0  # seconds
METRIC_SPECS = {
    "cpu": {
        "min": 0,
        "max": 100,
        "unit": "%",
        "volatility": 5
    },
    "memory": {
        "min": 0,
        "max": 100,
        "unit": "%",
        "volatility": 3
    },
    "bandwidth": {
        "min": 0,
        "max": 1000,
        "unit": "Mbps",
        "volatility": 50
    },
    "latency": {
        "min": 0,
        "max": 500,
        "unit": "ms",
        "volatility": 10
    }
}

# Alarm settings
MAX_ALARM_HISTORY = 50