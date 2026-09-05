"""Async Mailcow API client."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
import ipaddress
import socket
import ssl
from typing import Any
from urllib.parse import urlparse

from .const import (
    API_TEST_ENDPOINT,
    CONTAINERS_ENDPOINT,
    HOST_STATUS_ENDPOINT,
    DELETE_QUARANTINE_ENDPOINT,
    QUARANTINE_ENDPOINT,
    RELEASE_QUARANTINE_ENDPOINT,
)

import aiohttp
from aiohttp import ClientResponseError
from aiohttp.abc import AbstractResolver, ResolveResult


class MailcowError(Exception):
    """Base Mailcow error."""


class MailcowAuthError(MailcowError):
    """Authentication failed."""


class MailcowAccessBlockedError(MailcowError):
    """Access appears to be blocked by a proxy/CDN or HTTP policy."""


class MailcowConnectionError(MailcowError):
    """Unable to communicate with Mailcow."""


class MailcowInvalidResponseError(MailcowError):
    """Mailcow returned an unexpected response."""


class StaticResolver(AbstractResolver):
    """Resolve one configured hostname directly to an origin IP."""

    def __init__(self, hostname: str, origin_ip: str) -> None:
        self._hostname = hostname.lower()
        self._origin_ip = str(ipaddress.ip_address(origin_ip))
        self._family = (
            socket.AF_INET6 if ipaddress.ip_address(origin_ip).version == 6
            else socket.AF_INET
        )

    async def resolve(
        self,
        host: str,
        port: int = 0,
        family: socket.AddressFamily = socket.AF_INET,
    ) -> list[ResolveResult]:
        if host.lower() != self._hostname:
            raise OSError(f"Static resolver refuses unexpected hostname: {host}")

        return [
            {
                "hostname": host,
                "host": self._origin_ip,
                "port": port,
                "family": self._family,
                "proto": socket.IPPROTO_TCP,
                "flags": socket.AI_NUMERICHOST,
            }
        ]

    async def close(self) -> None:
        """Nothing to close."""


class MailcowApi:
    """Mailcow API wrapper."""

    def __init__(
        self,
        url: str,
        api_key: str,
        shared_session: aiohttp.ClientSession | None = None,
        origin_ip: str | None = None,
    ) -> None:
        self.url = url.rstrip("/")
        self.api_key = api_key
        self.origin_ip = origin_ip

        parsed = urlparse(self.url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            raise ValueError("A valid http(s) Mailcow URL is required")

        self.scheme = parsed.scheme
        self.hostname = parsed.hostname
        self.port = parsed.port or (443 if parsed.scheme == "https" else 80)

        self._owns_session = origin_ip is not None

        if origin_ip:
            # Keep the URL hostname unchanged. The custom resolver changes only
            # where the TCP connection goes, preserving HTTP Host + TLS SNI.
            resolver = StaticResolver(self.hostname, origin_ip)
            connector = aiohttp.TCPConnector(resolver=resolver)
            self._session = aiohttp.ClientSession(connector=connector)
        elif shared_session is not None:
            self._session = shared_session
        else:
            self._session = aiohttp.ClientSession()
            self._owns_session = True

    async def async_close(self) -> None:
        """Close only sessions created by this client."""
        if self._owns_session and not self._session.closed:
            await self._session.close()

    async def async_request(
        self,
        endpoint: str,
        method: str = "GET",
        payload: dict[str, Any] | list[Any] | None = None,
    ) -> Any:
        """Call a Mailcow v1 API endpoint."""
        endpoint = endpoint.lstrip("/")
        request_url = f"{self.url}/api/v1/{endpoint}"

        headers = {
            "X-API-Key": self.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        try:
            async with asyncio.timeout(15):
                async with self._session.request(
                    method,
                    request_url,
                    headers=headers,
                    json=payload,
                ) as response:
                    # 401 is reliably an authentication problem.
                    if response.status == 401:
                        raise MailcowAuthError("Mailcow rejected the API key")

                    # 403 is commonly what a proxy/CDN/access policy returns.
                    # Direct-origin setup can then be offered by the config flow.
                    if response.status == 403:
                        raise MailcowAccessBlockedError(
                            "Access was forbidden (HTTP 403)"
                        )

                    if response.status >= 400:
                        body = (await response.text())[:300]
                        raise MailcowConnectionError(
                            f"Mailcow returned HTTP {response.status}: {body}"
                        )

                    try:
                        return await response.json(content_type=None)
                    except (ValueError, aiohttp.ContentTypeError) as err:
                        raise MailcowInvalidResponseError(
                            "Mailcow did not return JSON"
                        ) from err

        except MailcowError:
            raise
        except (
            TimeoutError,
            asyncio.TimeoutError,
            aiohttp.ClientConnectionError,
            aiohttp.ClientConnectorError,
            aiohttp.ClientSSLError,
            aiohttp.ServerDisconnectedError,
            ClientResponseError,
        ) as err:
            raise MailcowConnectionError(str(err)) from err

    async def async_test_connection(self) -> None:
        """Validate API connectivity and authentication."""
        await self.async_request(API_TEST_ENDPOINT)

    async def async_get_containers(self) -> Any:
        """Return Mailcow container status data."""
        return await self.async_request(CONTAINERS_ENDPOINT)

    async def async_get_host_status(self) -> dict[str, Any]:
        """Return Mailcow host status data."""
        data = await self.async_request(HOST_STATUS_ENDPOINT)
        if not isinstance(data, dict):
            raise MailcowInvalidResponseError(
                "Host status endpoint returned an unexpected data type"
            )
        return data

    async def async_get_quarantine(self) -> list[dict[str, Any]]:
        """Return quarantine entries."""
        data = await self.async_request(QUARANTINE_ENDPOINT)
        if data is None:
            return []
        if not isinstance(data, list):
            raise MailcowInvalidResponseError(
                "Quarantine endpoint returned an unexpected data type"
            )
        return data

    async def async_get_quarantine_item_details(self, item_id: str) -> dict[str, Any]:
        """Return full details for one quarantine item using Mailcow's AJAX handler."""
        request_url = f"{self.url}/inc/ajax/qitem_details.php"
        headers = {"X-API-Key": self.api_key, "Accept": "application/json"}
        try:
            async with asyncio.timeout(15):
                async with self._session.get(
                    request_url,
                    headers=headers,
                    params={"id": str(item_id)},
                ) as response:
                    if response.status == 401:
                        raise MailcowAuthError("Mailcow rejected the API key")
                    if response.status == 403:
                        raise MailcowAccessBlockedError("Access was forbidden (HTTP 403)")
                    if response.status >= 400:
                        body = (await response.text())[:300]
                        raise MailcowConnectionError(
                            f"Mailcow returned HTTP {response.status}: {body}"
                        )
                    data = await response.json(content_type=None)
                    if not isinstance(data, dict):
                        raise MailcowInvalidResponseError(
                            "Quarantine details endpoint returned unexpected data"
                        )
                    return data
        except MailcowError:
            raise
        except (
            TimeoutError,
            asyncio.TimeoutError,
            aiohttp.ClientConnectionError,
            aiohttp.ClientConnectorError,
            aiohttp.ClientSSLError,
            aiohttp.ServerDisconnectedError,
            ClientResponseError,
            ValueError,
        ) as err:
            raise MailcowConnectionError(str(err)) from err

    async def async_release_quarantine_item(self, item_id: str) -> Any:
        """Release one quarantine item."""
        return await self.async_request(
            RELEASE_QUARANTINE_ENDPOINT,
            method="POST",
            payload={"items": [str(item_id)], "attr": {"action": "release"}},
        )

    async def async_delete_quarantine_item(self, item_id: str) -> Any:
        """Permanently delete one quarantine item."""
        return await self.async_request(
            DELETE_QUARANTINE_ENDPOINT,
            method="POST",
            payload=[str(item_id)],
        )

    async def async_get_certificate(self) -> dict[str, Any]:
        """Read the TLS certificate presented for the configured hostname."""
        if self.scheme != "https":
            return {
                "enabled": False,
                "days_remaining": None,
                "expires_at": None,
                "valid_from": None,
                "issuer": None,
                "subject": None,
            }

        connect_host = self.origin_ip or self.hostname
        context = ssl.create_default_context()

        try:
            async with asyncio.timeout(15):
                reader, writer = await asyncio.open_connection(
                    connect_host,
                    self.port,
                    ssl=context,
                    server_hostname=self.hostname,
                )
                try:
                    ssl_object = writer.get_extra_info("ssl_object")
                    if ssl_object is None:
                        raise MailcowConnectionError("No TLS session established")
                    cert = ssl_object.getpeercert()
                finally:
                    writer.close()
                    await writer.wait_closed()
        except MailcowError:
            raise
        except (
            TimeoutError,
            asyncio.TimeoutError,
            OSError,
            ssl.SSLError,
            ssl.CertificateError,
        ) as err:
            raise MailcowConnectionError(f"TLS certificate check failed: {err}") from err

        not_after = cert.get("notAfter")
        not_before = cert.get("notBefore")

        expires_at = (
            datetime.fromtimestamp(ssl.cert_time_to_seconds(not_after), tz=UTC)
            if not_after else None
        )
        valid_from = (
            datetime.fromtimestamp(ssl.cert_time_to_seconds(not_before), tz=UTC)
            if not_before else None
        )

        days_remaining = None
        if expires_at:
            days_remaining = int((expires_at - datetime.now(UTC)).total_seconds() // 86400)

        return {
            "enabled": True,
            "days_remaining": days_remaining,
            "expires_at": expires_at,
            "valid_from": valid_from,
            "issuer": _name_to_string(cert.get("issuer", ())),
            "subject": _name_to_string(cert.get("subject", ())),
        }


def _name_to_string(name: tuple[Any, ...]) -> str | None:
    """Convert ssl certificate subject/issuer tuples to readable text."""
    parts: list[str] = []
    for rdn in name:
        for key, value in rdn:
            parts.append(f"{key}={value}")
    return ", ".join(parts) if parts else None
