import ipaddress
import socket
from urllib.parse import urlparse

from app.core.errors import SSRFValidationError

# Blocked IP Networks for SSRF Defense
BLOCKED_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),          # Current network
    ipaddress.ip_network("10.0.0.0/8"),         # RFC 1918 Private
    ipaddress.ip_network("100.64.0.0/10"),      # Carrier-grade NAT
    ipaddress.ip_network("127.0.0.0/8"),        # Loopback
    ipaddress.ip_network("169.254.0.0/16"),     # Link-local / Cloud metadata (AWS, GCP, Azure)
    ipaddress.ip_network("172.16.0.0/12"),      # RFC 1918 Private
    ipaddress.ip_network("192.0.0.0/24"),       # IETF Protocol Assignments
    ipaddress.ip_network("192.0.2.0/24"),       # TEST-NET-1
    ipaddress.ip_network("192.168.0.0/16"),     # RFC 1918 Private
    ipaddress.ip_network("198.18.0.0/15"),      # Benchmark testing
    ipaddress.ip_network("198.51.100.0/24"),    # TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),     # TEST-NET-3
    ipaddress.ip_network("224.0.0.0/4"),        # Multicast
    ipaddress.ip_network("240.0.0.0/4"),        # Reserved / Future use
    ipaddress.ip_network("255.255.255.255/32"), # Broadcast
    # IPv6 ranges
    ipaddress.ip_network("::1/128"),            # Loopback
    ipaddress.ip_network("::/128"),             # Unspecified
    ipaddress.ip_network("fc00::/7"),           # Unique local address (ULA)
    ipaddress.ip_network("fe80::/10"),          # Link-local
    ipaddress.ip_network("ff00::/8"),           # Multicast
]

BLOCKED_HOSTNAMES = {
    "localhost",
    "metadata.google.internal",
    "instance-data",
    "metadata",
    "kubernetes.default",
    "docker.for.win.localhost",
    "host.docker.internal",
}


def validate_url_ssrf(url_string: str) -> str:
    """
    Validates a URL against Server-Side Request Forgery (SSRF) threats.
    Performs DNS resolution and asserts that all returned IP addresses are public.
    """
    if not url_string:
        raise SSRFValidationError("URL cannot be empty.")

    try:
        parsed = urlparse(url_string.strip())
    except (ValueError, TypeError, AttributeError) as exc:
        raise SSRFValidationError(f"Invalid URL structure: {exc}") from exc

    # Scheme Validation
    if parsed.scheme.lower() not in ("http", "https"):
        raise SSRFValidationError(
            f"Unsupported scheme '{parsed.scheme}'. Only http:// and https:// are permitted."
        )

    hostname = parsed.hostname
    if not hostname:
        raise SSRFValidationError("URL is missing a valid hostname.")

    clean_hostname = hostname.lower().strip()

    # Blocked hostname literal check
    if clean_hostname in BLOCKED_HOSTNAMES or clean_hostname.endswith(".local"):
        raise SSRFValidationError(f"Access to host '{clean_hostname}' is strictly blocked.")

    # Try parsing hostname directly as IP
    try:
        ip = ipaddress.ip_address(clean_hostname)
        _check_ip_safety(ip)
        return url_string
    except ValueError:
        # Not a direct IP literal, proceed to DNS resolution
        pass

    # Resolve all IPv4 and IPv6 addresses for hostname
    try:
        addr_info = socket.getaddrinfo(clean_hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise SSRFValidationError(f"Unable to resolve hostname '{clean_hostname}': {exc}")

    if not addr_info:
        raise SSRFValidationError(f"No IP addresses resolved for hostname '{clean_hostname}'.")

    for family, _, _, _, sockaddr in addr_info:
        ip_str = sockaddr[0]
        try:
            ip = ipaddress.ip_address(ip_str)
            _check_ip_safety(ip)
        except ValueError:
            raise SSRFValidationError(f"Invalid resolved IP '{ip_str}'.")

    return url_string


def _check_ip_safety(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> None:
    """Asserts that an IP address does not fall into any blocked subnet."""
    if ip.is_loopback:
        raise SSRFValidationError(f"Access to loopback IP {ip} is blocked.")
    if ip.is_private:
        raise SSRFValidationError(f"Access to private IP {ip} is blocked.")
    if ip.is_link_local:
        raise SSRFValidationError(f"Access to link-local IP {ip} is blocked.")
    if ip.is_multicast:
        raise SSRFValidationError(f"Access to multicast IP {ip} is blocked.")
    if ip.is_unspecified:
        raise SSRFValidationError(f"Access to unspecified IP {ip} is blocked.")

    for blocked in BLOCKED_NETWORKS:
        if ip in blocked:
            raise SSRFValidationError(f"Access to protected IP range {blocked} ({ip}) is blocked.")
