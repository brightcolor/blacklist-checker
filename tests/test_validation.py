import pytest

from app.services.validation import ValidationError, normalize_target


def test_normalize_ipv4():
    assert normalize_target("ipv4", " 203.0.113.1 ") == "203.0.113.1"


def test_normalize_domain():
    assert normalize_target("domain", "Example.org.") == "example.org"


@pytest.mark.parametrize("kind,value", [("ipv4", "300.1.1.1"), ("domain", "bad_domain")])
def test_normalize_invalid(kind, value):
    with pytest.raises(ValidationError):
        normalize_target(kind, value)
