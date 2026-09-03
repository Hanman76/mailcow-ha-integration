# Mailcow for Home Assistant

A custom Home Assistant integration for monitoring and managing a Mailcow server.

The goal of this project is to provide native Mailcow functionality in Home Assistant without relying on shell commands, REST sensors, or external scripts.

> [!IMPORTANT]
> This integration is currently in early development. Version 0.1.0 provides the initial monitoring functionality. More Mailcow management features are planned.

## Features

### Available in v0.1.0

- Mailcow API connection monitoring
- Quarantine message count
- TLS certificate expiry monitoring
- Certificate information including issuer and validity dates
- Configuration through the Home Assistant UI
- Support for Mailcow servers behind Cloudflare, CDNs, and reverse proxies
- Direct server connection while preserving the Mailcow hostname for TLS validation
- Automatic coordinator-based polling

## Planned features

Future versions are planned to include:

- Recent quarantine messages
- Release quarantined messages
- Delete quarantined messages
- Mail queue monitoring
- Auto-delete rules
- Create, edit, enable and disable rules
- Additional Mailcow health and status sensors

## Installation

### Manual installation

Copy:

custom_components/mailcow/

to:

/config/custom_components/mailcow/

Restart Home Assistant.

Then go to:

Settings → Devices & services → Add integration → Mailcow

Enter your Mailcow hostname and API key.

### HACS

HACS installation is planned but is not yet officially supported.

## Cloudflare / reverse proxy support

The integration first attempts to connect using the normal Mailcow URL.

If the connection fails, the setup process can configure a direct connection to the Mailcow server. This is useful when Cloudflare, a CDN, or another reverse proxy prevents Home Assistant from accessing the Mailcow API.

When using this mode, the integration connects directly to the server IP while retaining the Mailcow hostname for HTTPS/TLS validation.

## Entities

Version 0.1.0 currently creates:

- API connection
- Quarantine count
- Certificate

## Requirements

- Home Assistant
- A working Mailcow installation
- Mailcow API access
- A Mailcow API key

## Security

Your Mailcow API key is entered through the Home Assistant configuration flow and is not stored in the integration source code.

Never commit API keys, passwords, server credentials, or other secrets to this repository.

## Development status

This project is under active development.

The initial v0.1.0 release focuses on establishing a reliable connection between Home Assistant and Mailcow, including installations using Cloudflare or another reverse proxy.

Quarantine management is planned as the next major feature.

## Contributing

Issues, bug reports, feature requests, and pull requests are welcome.

If you encounter a problem, please include your Home Assistant version, Mailcow version, and relevant Home Assistant log messages. Do not include API keys or other credentials.

## License

MIT
