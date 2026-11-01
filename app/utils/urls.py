"""URL helpers. website_id is derived from the normalized link."""

import hashlib
import re
from urllib.parse import urlparse

_SCHEME_RE = re.compile(r"^[a-z][a-z0-9+.\-]*://")


def normalize_link(url: str) -> str:
    """Reduce a URL to a canonical form so near-duplicates map to the same key.

    https://www.Example.com/  ->  example.com
    http://example.com        ->  example.com

    NOTE: website_id values are hashes of this output. Changing this function
    changes every id, so treat it as frozen once data has been loaded.
    """
    url = url.strip().lower()
    if not _SCHEME_RE.match(url):
        url = "http://" + url
    parsed = urlparse(url)
    host = parsed.netloc
    if host.startswith("www."):
        host = host[4:]
    path = parsed.path.rstrip("/")
    query = f"?{parsed.query}" if parsed.query else ""
    return f"{host}{path}{query}"


def make_website_id(url: str) -> str:
    """Deterministic 32-character ID derived from the normalized link."""
    return hashlib.sha256(normalize_link(url).encode("utf-8")).hexdigest()[:32]


def has_valid_host(url: object) -> bool:
    """True if the link has something that looks like a domain (contains a dot)."""
    if not isinstance(url, str):
        return False
    try:
        normalized = normalize_link(url)
    except ValueError:  # e.g. malformed IPv6 brackets
        return False
    host = re.split(r"[/?#]", normalized, maxsplit=1)[0]
    return bool(host) and "." in host and " " not in host
