"""Constants for the Mailcow integration."""

from datetime import timedelta

DOMAIN = "mailcow"
PLATFORMS = ["binary_sensor", "sensor"]

CONF_URL = "url"
CONF_API_KEY = "api_key"
CONF_ORIGIN_IP = "origin_ip"

DEFAULT_SCAN_INTERVAL = timedelta(minutes=5)
API_TEST_ENDPOINT = "get/status/containers"
QUARANTINE_ENDPOINT = "get/quarantine/all"
