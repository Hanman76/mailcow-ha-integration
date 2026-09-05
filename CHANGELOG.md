# Changelog

All notable changes to this project will be documented in this file.

## 0.2.0 - Unreleased

### Added

- Persistent recent quarantine history with up to 20 entries
- Native Home Assistant actions for viewing, releasing, and deleting quarantine items
- Quarantine item details support
- API response time sensor
- Container health problem binary sensor
- Containers running sensor
- CPU load sensor
- Memory usage sensor
- Uptime sensor
- Diagnostics support
- Current quarantine messages exposed as sensor attributes

### Changed

- Operational Mailcow data now refreshes every 60 seconds
- TLS certificate data refreshes separately every 12 hours
- Recent quarantine history is stored persistently in Home Assistant
- Quarantine history entries can be updated to show Released or Deleted status
- Expanded Mailcow host monitoring using the Mailcow API

## 0.1.0

### Added

- Initial tested foundation
- UI-based Mailcow configuration
- Mailcow URL and API key configuration
- Cloudflare/CDN/direct-origin connection support
- API connectivity binary sensor
- Quarantine count sensor
- TLS certificate monitoring
- Home Assistant device metadata and local branding
