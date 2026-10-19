"""Regression test for the production Amplify CORS allowlist pattern."""
from pathlib import Path
import re


def test_amplify_cors_regex_matches_https_amplify_hosts_only():
    source = Path(__file__).parents[1].joinpath("app", "main.py").read_text()
    match = re.search(r'allow_origin_regex\s*=\s*r"([^"]+)"', source)
    assert match, "CORS origin regex must be explicitly configured"

    origin_pattern = re.compile(match.group(1))
    assert origin_pattern.fullmatch("https://main.d1qcu413dz9f9e.amplifyapp.com")
    assert origin_pattern.fullmatch("https://feature-123.amplifyapp.com")
    assert not origin_pattern.fullmatch("http://main.amplifyapp.com")
    assert not origin_pattern.fullmatch("https://amplifyapp.com.attacker.example")
    assert not origin_pattern.fullmatch("https://amplifyapp.com")
