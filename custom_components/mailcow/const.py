"""Constants for the Mailcow integration."""

from datetime import timedelta

DOMAIN = "mailcow"
PLATFORMS = ["binary_sensor", "sensor"]

CONF_URL = "url"
CONF_API_KEY = "api_key"
CONF_ORIGIN_IP = "origin_ip"

OPERATIONAL_SCAN_INTERVAL = timedelta(minutes=1)
CERTIFICATE_SCAN_INTERVAL = timedelta(hours=12)

API_TEST_ENDPOINT = "get/status/containers"
CONTAINERS_ENDPOINT = "get/status/containers"
HOST_STATUS_ENDPOINT = "get/status/host"
QUARANTINE_ENDPOINT = "get/quarantine/all"
RELEASE_QUARANTINE_ENDPOINT = "edit/qitem"
DELETE_QUARANTINE_ENDPOINT = "delete/qitem"

RECENT_QUARANTINE_LIMIT = 20
HISTORY_STORAGE_VERSION = 1
