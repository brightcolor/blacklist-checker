import ipaddress
import re
from dataclasses import dataclass

import dns.asyncresolver
import dns.exception
import dns.reversename

from app.core.config import get_settings
from app.models.monitor import CheckStatus
from app.models.rbl import RBLList, RBLListType

settings = get_settings()


@dataclass
class DNSCheckOutcome:
    list_id: int
    list_name: str
    dns_zone: str
    status: CheckStatus
    answer_code: str | None = None
    txt_record: str | None = None
    raw_error: str | None = None


class DNSLookupEngine:
    def __init__(self) -> None:
        self.resolver = dns.asyncresolver.Resolver(configure=True)
        self.resolver.lifetime = settings.dns_default_timeout

    @staticmethod
    def _reverse_ipv4(ip: str) -> str:
        return ".".join(reversed(ip.split(".")))

    @staticmethod
    def _reverse_ipv6(ip: str) -> str:
        exploded = ipaddress.IPv6Address(ip).exploded.replace(":", "")
        return ".".join(reversed(exploded))

    @staticmethod
    def _accepts_return_code(rbl: RBLList, answer_code: str | None) -> bool:
        if not answer_code:
            return True
        if not rbl.return_code_regex:
            return True
        return bool(re.match(rbl.return_code_regex, answer_code))

    async def _resolve_a(self, query: str) -> tuple[str | None, str | None]:
        answers = await self.resolver.resolve(query, "A")
        value = str(answers[0]) if answers else None
        return value, None

    async def _resolve_txt(self, query: str) -> str | None:
        try:
            txt_answers = await self.resolver.resolve(query, "TXT")
        except Exception:
            return None
        txt_parts: list[str] = []
        for ans in txt_answers:
            txt_parts.extend(p.decode("utf-8", errors="ignore") for p in ans.strings)
        return " ".join(txt_parts) if txt_parts else None

    async def run_list_check(self, target_type: str, target_value: str, rbl: RBLList) -> DNSCheckOutcome:
        if not rbl.is_enabled:
            return DNSCheckOutcome(rbl.id, rbl.name, rbl.dns_zone, CheckStatus.DISABLED)
        query = ""
        try:
            if target_type == "ipv4":
                if not rbl.supports_ipv4:
                    return DNSCheckOutcome(rbl.id, rbl.name, rbl.dns_zone, CheckStatus.DISABLED)
                query = f"{self._reverse_ipv4(target_value)}.{rbl.dns_zone}"
            elif target_type == "ipv6":
                if not rbl.supports_ipv6:
                    return DNSCheckOutcome(rbl.id, rbl.name, rbl.dns_zone, CheckStatus.DISABLED)
                query = f"{self._reverse_ipv6(target_value)}.{rbl.dns_zone}"
            elif target_type in {"domain", "hostname"}:
                if target_type == "domain" and not rbl.supports_domain:
                    return DNSCheckOutcome(rbl.id, rbl.name, rbl.dns_zone, CheckStatus.DISABLED)
                if target_type == "hostname" and not (rbl.supports_hostname or rbl.supports_domain):
                    return DNSCheckOutcome(rbl.id, rbl.name, rbl.dns_zone, CheckStatus.DISABLED)
                query = f"{target_value}.{rbl.dns_zone}"
            else:
                return DNSCheckOutcome(
                    rbl.id, rbl.name, rbl.dns_zone, CheckStatus.ERROR, raw_error="unsupported_target"
                )

            answer_code, _ = await self._resolve_a(query)
            txt = await self._resolve_txt(query)
            listed = self._accepts_return_code(rbl, answer_code)

            if listed:
                status = CheckStatus.LISTED
                if rbl.list_type == RBLListType.WHITELIST:
                    status = CheckStatus.CLEAN
            else:
                status = CheckStatus.CLEAN
                if rbl.is_degraded:
                    status = CheckStatus.DEGRADED

            return DNSCheckOutcome(
                list_id=rbl.id,
                list_name=rbl.name,
                dns_zone=rbl.dns_zone,
                status=status,
                answer_code=answer_code,
                txt_record=txt,
            )
        except dns.resolver.NXDOMAIN:
            return DNSCheckOutcome(rbl.id, rbl.name, rbl.dns_zone, CheckStatus.CLEAN)
        except dns.resolver.NoAnswer:
            return DNSCheckOutcome(rbl.id, rbl.name, rbl.dns_zone, CheckStatus.CLEAN)
        except dns.exception.Timeout:
            return DNSCheckOutcome(
                rbl.id, rbl.name, rbl.dns_zone, CheckStatus.TIMEOUT, raw_error="timeout"
            )
        except Exception as exc:
            return DNSCheckOutcome(
                rbl.id,
                rbl.name,
                rbl.dns_zone,
                CheckStatus.ERROR,
                raw_error=str(exc),
            )

    async def fcrdns(self, ip: str) -> dict[str, str | bool | None]:
        try:
            reverse_name = dns.reversename.from_address(ip)
            ptr_answers = await self.resolver.resolve(reverse_name, "PTR")
            ptr_target = str(ptr_answers[0]).rstrip(".") if ptr_answers else None
            if not ptr_target:
                return {"ok": False, "ptr": None, "reason": "missing_ptr"}
            a_answers = await self.resolver.resolve(ptr_target, "A")
            matches = ip in [str(a) for a in a_answers]
            return {"ok": matches, "ptr": ptr_target, "reason": None if matches else "ip_not_in_forward"}
        except Exception as exc:
            return {"ok": False, "ptr": None, "reason": str(exc)}
