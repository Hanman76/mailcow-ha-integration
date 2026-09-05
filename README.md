# Mailcow Home Assistant Integration

A custom Home Assistant integration for monitoring and managing Mailcow servers.

## 🚧 Development Status

> **Please do not install this integration yet.**
>
> Version 0.2.0 is the current development release and is not yet intended for general use.
> The integration is under active development, with additional functionality and improvements planned for version 0.3.0.
>
> ⭐ **Keep an eye on this repository for updates.**

## Features in v0.2.0

### Mailcow monitoring

- UI-based setup through Home Assistant
- Mailcow URL and API key configuration
- HTTPS pre-filled during setup
- Normal API connection tested first
- Guided fallback for Mailcow installations behind Cloudflare, a CDN, or another proxy
- Optional direct Mailcow server IP while preserving the hostname for HTTPS/TLS
- API connectivity binary sensor
- API response time sensor
- Container health problem binary sensor
- Containers running sensor
- CPU load sensor
- Memory usage sensor
- Uptime sensor

### Quarantine

- Current quarantine count
- Current quarantine messages exposed as sensor attributes
- Persistent recent quarantine history
- Up to 20 recent quarantine entries retained in Home Assistant
- Quarantine item details
- Native Home Assistant action for viewing quarantine items
- Native Home Assistant action for releasing quarantine items
- Native Home Assistant action for deleting quarantine items
- Quarantine history status tracking for released and deleted messages

### TLS certificate monitoring

- TLS certificate days-remaining sensor
- Certificate issuer
- Certificate subject
- Certificate valid-from date
- Certificate expiry date
- Separate 12-hour certificate refresh interval
- Direct-origin certificate checking while preserving hostname/SNI when configured

### Home Assistant integration

- Central asynchronous Mailcow API client
- Home Assistant `DataUpdateCoordinator`
- Operational Mailcow data refreshed every 60 seconds
- Persistent quarantine history using Home Assistant storage
- Diagnostics support with sensitive configuration values redacted
- Local Home Assistant brand icon/logo
- Home Assistant device metadata (`Mailcow Server` by `mailcow`)

## Planned for v0.3.0

Development for v0.3.0 is planned to expand Mailcow management capabilities further.

Areas under consideration include:

- Richer quarantine management
- Whitelist and blacklist management
- Mail queue monitoring and management
- Configurable quarantine rules
- Suggested rules based on quarantine history and message patterns
- Additional Mailcow health and status information
- Further Home Assistant UI and action improvements

Features listed here are planned or under consideration and may change during development.

## Installation for testing

> **Development/testing only.**
>
> Installation is not currently recommended for general use.

### HACS

The integration can be installed as a custom repository in HACS for development and testing.

Add this repository to HACS as an **Integration**, then install **Mailcow**.

Restart Home Assistant after installation.

Then go to:

**Settings → Devices & services → Add integration → Mailcow**

### Manual installation

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

## Configuration

Enter your Mailcow hostname and API key during setup.

The integration first attempts to connect normally to the configured Mailcow hostname.

If the normal API connection fails, the setup flow asks whether the Mailcow server is
behind Cloudflare, a CDN, or another proxy.

If so, you can enter the public IP address of the Mailcow server. The integration connects
directly to that IP while retaining the configured Mailcow hostname for HTTPS certificate
validation and TLS SNI.

This makes it possible to monitor the Mailcow origin server directly without disabling
HTTPS certificate validation.

## Mailcow API

Version 0.2.0 uses the Mailcow API for monitoring and quarantine functionality.

Examples of endpoints used include:

### Container status

```text
GET /api/v1/get/status/containers
```

### Host status

```text
GET /api/v1/get/status/host
```

Used for CPU load, memory usage, and uptime information.

### Quarantine

```text
GET /api/v1/get/quarantine/all
```

### Release quarantine item

```text
POST /api/v1/edit/qitem
```

### Delete quarantine item

```text
POST /api/v1/delete/qitem
```

Quarantine message details are retrieved separately when requested.

## Polling

Operational Mailcow information is refreshed every:

```text
60 seconds
```

TLS certificate information is refreshed every:

```text
12 hours
```

The certificate check uses a real TLS connection to inspect the certificate presented by
the configured Mailcow server.

When direct-origin mode is configured, the integration connects to the origin IP while
using the Mailcow hostname for TLS SNI and certificate validation.

## Security

Never commit your Mailcow API key, server credentials, or other secrets to this repository.

Configuration values entered through Home Assistant are stored in the Home Assistant
config entry and are not hard-coded in the integration.

Diagnostics redact the configured Mailcow API key.

For monitoring functionality, use a Mailcow API key with only the permissions required
for the functionality you intend to use.

Actions that modify Mailcow data, such as releasing or deleting quarantine items, require
appropriate Mailcow API permissions.

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
    ├── diagnostics.py
    ├── entity.py
    ├── history.py
    ├── manifest.json
    ├── sensor.py
    ├── services.yaml
    ├── brand/
    │   ├── icon.png
    │   ├── icon@2x.png
    │   ├── logo.png
    │   └── logo@2x.png
    └── translations/
        └── en.json
```

## Bug reports and feature requests

Bug reports and feature requests are welcome.

The integration is still under active development, so please include relevant Home Assistant
and Mailcow version information when reporting a problem.

## ☕ Support

If you find this project useful and would like to support its development, you can buy me a coffee.

[![Buy Me a Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://buymeacoffee.com/hanman76)

## License

MIT
