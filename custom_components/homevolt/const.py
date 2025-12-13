"""Constants for the Homevolt integration."""

from __future__ import annotations

DOMAIN = "homevolt"
PLATFORMS = ["sensor", "binary_sensor"]

CONF_USE_HTTPS = "use_https"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_NAME = "Homevolt"
DEFAULT_PORT = 443
DEFAULT_VERIFY_SSL = False
DEFAULT_USE_HTTPS = True
DEFAULT_SCAN_INTERVAL = 30
