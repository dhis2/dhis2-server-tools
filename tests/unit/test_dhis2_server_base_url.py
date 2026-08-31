"""URL construction for dhis.conf server.base.url."""
import importlib.util
import sys
from pathlib import Path

import pytest

_FILTERS = Path(__file__).resolve().parents[2] / "deploy" / "filter_plugins" / "custom_filters.py"
_spec = importlib.util.spec_from_file_location("custom_filters", _FILTERS)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["custom_filters"] = _mod
_spec.loader.exec_module(_mod)

dhis2_server_base_url = _mod.dhis2_server_base_url
AnsibleFilterError = _mod.AnsibleFilterError


@pytest.mark.parametrize(
    "override,fqdn,context,port,expected",
    [
        ("", "hmis.moh.gov", "dhis", 443, "https://hmis.moh.gov/dhis"),
        ("", "same.example.org", "hmis", 443, "https://same.example.org/hmis"),
        ("", "same.example.org", "training", 443, "https://same.example.org/training"),
        ("", "fqdn.example.org", "dhis2", 443, "https://fqdn.example.org/dhis2"),
        ("", "fqdn.example.org", "ROOT", 443, "https://fqdn.example.org"),
        ("", "fqdn.example.org", "dhis", 8443, "https://fqdn.example.org:8443/dhis"),
        ("", "", "dhis", 443, ""),
        ("", "   ", "dhis", 443, ""),
        (
            "https://cdn.example.org/dhis/",
            "ignored.example.org",
            "dhis",
            443,
            "https://cdn.example.org/dhis",
        ),
        (
            "https://cdn.example.org:443/dhis",
            "",
            "ROOT",
            443,
            "https://cdn.example.org/dhis",
        ),
        ("", "play.example.org", 2.4, 443, "https://play.example.org/2.40"),
        ("", "play.example.org", "", 443, "https://play.example.org"),
        ("", "hmis.moh.gov", "dhis", "443", "https://hmis.moh.gov/dhis"),
    ],
)
def test_builds_public_url(override, fqdn, context, port, expected):
    assert dhis2_server_base_url(override, fqdn, context, port) == expected


@pytest.mark.parametrize(
    "override,fqdn,context,port",
    [
        ("http://insecure.example.org/dhis", "", "dhis", 443),
        ("https://localhost/dhis", "", "dhis", 443),
        ("https://127.0.0.1/dhis", "", "dhis", 443),
        ("https://user:pass@evil.example.org/dhis", "", "dhis", 443),
        ("https://ok.example.org/dhis?next=https://evil", "", "dhis", 443),
        ("https://ok.example.org/dhis#frag", "", "dhis", 443),
        ("https://ok.example.org/dhis\nconnection.password=x", "", "dhis", 443),
        ("javascript:alert(1)", "", "dhis", 443),
        ("", "https://not-a-host.example.org", "dhis", 443),
        ("", "host.example.org:8443", "dhis", 443),
        ("", "ok.example.org", "../etc", 443),
        ("", "ok.example.org", "foo/bar", 443),
        ("", "ok.example.org", "dhis", 0),
        ("", "ok.example.org", "dhis", 70000),
        ("", "ok.example.org", "dhis", "none"),
        ("https://ok.example.org/dhis extra", "", "dhis", 443),
        ("https://0.0.0.0/dhis", "", "dhis", 443),
        ("https://[::]/dhis", "", "dhis", 443),
        ("https://127.1/dhis", "", "dhis", 443),
        ("https://example.com:99999/dhis", "", "dhis", 443),
        ("https://example.com:abc/dhis", "", "dhis", 443),
        ("https://ok.example.org/dhis\x1b", "", "dhis", 443),
        ("https://ok.example.org/dhis\x7f", "", "dhis", 443),
        ("", "2001:db8::1", "dhis", 443),
        ("", "0.0.0.0", "dhis", 443),
        ("", "127.1", "dhis", 443),
    ],
)
def test_rejects_unsafe_values(override, fqdn, context, port):
    with pytest.raises(AnsibleFilterError):
        dhis2_server_base_url(override, fqdn, context, port)
