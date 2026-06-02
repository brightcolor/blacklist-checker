import ipaddress
import re

DOMAIN_RE = re.compile(r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*\.?$")
HOSTNAME_RE = DOMAIN_RE


class ValidationError(Exception):
    pass


def normalize_target(target_type: str, target_value: str) -> str:
    raw = target_value.strip().lower().rstrip(".")
    if target_type == "ipv4":
        try:
            return str(ipaddress.IPv4Address(raw))
        except ipaddress.AddressValueError as exc:
            raise ValidationError("Invalid IPv4") from exc
    if target_type == "ipv6":
        try:
            return str(ipaddress.IPv6Address(raw))
        except ipaddress.AddressValueError as exc:
            raise ValidationError("Invalid IPv6") from exc
    if target_type == "domain":
        if not DOMAIN_RE.match(raw):
            raise ValidationError("Invalid domain")
        return raw
    if target_type == "hostname":
        if not HOSTNAME_RE.match(raw):
            raise ValidationError("Invalid hostname")
        return raw
    raise ValidationError("Unsupported target type")
