"""Connect to validated addresses without a second DNS lookup.

HTTPS keeps the original hostname for certificate verification and SNI.
Transport policy is applied at connection time, including on every retry.
"""
from __future__ import annotations

import http.client
import ipaddress
import socket
import urllib.request
from typing import Any


def validate_address(address: str) -> None:
    addr = ipaddress.ip_address(address)
    if isinstance(addr, ipaddress.IPv6Address) and addr.ipv4_mapped is not None:
        addr = addr.ipv4_mapped
    if not addr.is_global or addr.is_multicast:
        raise ValueError(f"URL resolves to private/reserved IP {addr}. Use a public endpoint.")


def _connect_public(address: Any, timeout: Any, source_address: Any = None) -> socket.socket:
    host, port = address
    resolved = socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM)
    if not resolved:
        raise OSError("Endpoint DNS returned no addresses")
    # Reject mixed public/private answers rather than choosing a lucky address.
    for _, _, _, _, sockaddr in resolved:
        validate_address(sockaddr[0])
    last_error = None
    for family, socktype, proto, _, sockaddr in resolved:
        sock = socket.socket(family, socktype, proto)
        try:
            sock.settimeout(timeout)
            if source_address:
                sock.bind(source_address)
            sock.connect(sockaddr)
            return sock
        except OSError as exc:
            last_error = exc
            sock.close()
    raise OSError("Could not connect to validated endpoint") from last_error


class _PublicHTTPConnection(http.client.HTTPConnection):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._create_connection = _connect_public


class _PublicHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._create_connection = _connect_public


class PublicHTTPHandler(urllib.request.HTTPHandler):
    def http_open(self, req: Any) -> Any:
        connection = (http.client.HTTPConnection if getattr(req, "_allow_private", False)
                      else _PublicHTTPConnection)
        return self.do_open(connection, req)


class PublicHTTPSHandler(urllib.request.HTTPSHandler):
    def https_open(self, req: Any) -> Any:
        connection = (http.client.HTTPSConnection if getattr(req, "_allow_private", False)
                      else _PublicHTTPSConnection)
        return self.do_open(connection, req, context=self._context)
