import json
from pathlib import Path

from sqlalchemy import select

from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.rbl import RBLList, RBLListType
from app.models.user import User, UserRole

ROOT = Path(__file__).resolve().parent
SEED_FILE = ROOT / "data" / "rbl_seed.json"


def seed_user(db):
    admin = db.execute(select(User).where(User.email == "admin@example.com")).scalars().first()
    if not admin:
        db.add(
            User(
                email="admin@example.com",
                password_hash=get_password_hash("ChangeMeNow123!"),
                role=UserRole.ADMIN,
            )
        )


def seed_lists(db):
    payload = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    for item in payload:
        exists = db.execute(select(RBLList).where(RBLList.dns_zone == item["dns_zone"])).scalars().first()
        if exists:
            continue
        db.add(
            RBLList(
                name=item["name"],
                list_type=RBLListType(item["list_type"]),
                dns_zone=item["dns_zone"],
                supports_ipv4=item["supports_ipv4"],
                supports_ipv6=item["supports_ipv6"],
                supports_domain=item["supports_domain"],
                supports_hostname=item["supports_hostname"],
                description=item.get("description"),
                url=item.get("url"),
                delist_url=item.get("delist_url"),
                return_code_regex=item.get("return_code_regex"),
                severity=item.get("severity", 2),
                priority=item.get("priority", 100),
                timeout_seconds=item.get("timeout_seconds", 3),
                is_enabled=item.get("is_enabled", True),
                health_score=item.get("health_score", 100),
                is_degraded=item.get("is_degraded", False),
            )
        )


def main():
    db = SessionLocal()
    try:
        seed_user(db)
        seed_lists(db)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
