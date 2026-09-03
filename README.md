# Mailcow Home Assistant Integration

A custom Home Assistant integration for monitoring Mailcow servers.

> **Status:** Early development. Version 0.1.0 is the first tested foundation.

## Features in v0.1.0

- UI-based setup through Home Assistant
- Mailcow URL and API key configuration
- HTTPS pre-filled during setup
- Normal API connection tested first
- Guided fallback for Mailcow installations behind Cloudflare, a CDN, or another proxy
- Optional direct Mailcow server IP while preserving the hostname for HTTPS/TLS
- API connectivity binary sensor
- Quarantine count sensor
- TLS certificate days-remaining sensor
- TLS certificate metadata including issuer, subject, valid-from, and expiry
- Central asynchronous API client and Home Assistant `DataUpdateCoordinator`
- Local Home Assistant brand icon/logo
- Clean Home Assistant device metadata (`Mailcow Server` by `mailcow`)

## Planned

Future versions are intended to add richer quarantine management, release/delete actions,
mail queue functionality, and configurable auto-delete rules.

## Installation for testing

Copy:

```text
custom_components/mailcow/
```

to:

```text
/config/custom_components/mailcow/
```

Restart Home Assistant, then go to:

**Settings → Devices & services → Add integration → Mailcow**

Enter your Mailcow hostname and API key.

If the normal API connection fails, the setup flow asks whether the Mailcow server is
behind Cloudflare, a CDN, or another proxy. If so, enter the public IP address of the
Mailcow server. The integration connects to that IP while retaining the configured
Mailcow hostname for HTTPS certificate validation and TLS SNI.

## API endpoints used in v0.1.0

Connection test:

```text
GET /api/v1/get/status/containers
```

Quarantine:

```text
GET /api/v1/get/quarantine/all
```

## Security

Never commit your Mailcow API key, server credentials, or other secrets to this repository.

Configuration values entered through Home Assistant are stored in the Home Assistant
config entry and are not hard-coded in the integration.

## Repository structure

```text
custom_components/
└── mailcow/
    ├── __init__.py
    ├── api.py
    ├── binary_sensor.py
    ├── config_flow.py
    ├── const.py
    ├── coordinator.py
    ├── entity.py
    ├── manifest.json
    ├── sensor.py
    ├── brand/
    │   ├── icon.png
    │   ├── icon@2x.png
    │   ├── logo.png
    │   └── logo@2x.png
    └── translations/
        └── en.json
```

## License

MIT
