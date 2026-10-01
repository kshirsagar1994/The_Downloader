# Universal Media Downloader — Security Architecture & Threat Model

## 1. Security Overview

The Universal Media Downloader processes untrusted user-submitted input (URLs, requested formats, quality selections, image indices) and performs network fetches and media transcode operations. This makes security, network perimeter isolation, and process safety non-negotiable architectural requirements.

---

## 2. Server-Side Request Forgery (SSRF) Defense

### Threat
An attacker submits URLs pointing to internal infrastructure, loopback devices, private subnets, cloud instance metadata services (`169.254.169.254`), container bridge networks, or internal Kubernetes/Docker services.

### Multi-Layered SSRF Mitigation Engine
1. **Scheme Whitelisting**:
   - Only `http://` and `https://` schemes are permitted.
   - All other schemes (`file://`, `ftp://`, `gopher://`, `data://`, `dict://`, `ldap://`, `php://`) are rejected at schema validation.

2. **Pre-flight DNS & IP Range Resolution**:
   - Before handing any URL to `yt-dlp` or the HTTP client, the hostname is resolved to IPv4 / IPv6 addresses.
   - Every resolved IP address is verified against prohibited CIDR blocks using Python's `ipaddress` standard library:
     - `127.0.0.0/8` (IPv4 Loopback)
     - `::1/128` (IPv6 Loopback)
     - `10.0.0.0/8` (Private Class A)
     - `172.16.0.0/12` (Private Class B)
     - `192.168.0.0/16` (Private Class C)
     - `169.254.0.0/16` (IPv4 Link-Local / Cloud Metadata)
     - `fe80::/10` (IPv6 Link-Local)
     - `fc00::/7` (IPv6 Unique Local)
     - `0.0.0.0/8` (Current Network)
     - `224.0.0.0/4` (Multicast)
     - `240.0.0.0/4` (Reserved)
     - `100.64.0.0/10` (Carrier-Grade NAT)

3. **Redirect Validation & Re-evaluation**:
   - Downloader clients follow redirects using a custom transport adapter that validates every intermediate `Location:` header against the SSRF IP blocklist before making the subsequent request.

4. **DNS Rebinding Prevention**:
   - IP pinning or immediate socket connection to the pre-verified IP is enforced to prevent DNS rebinding attacks where the domain resolves to a public IP on pre-flight and an internal IP during fetching.

---

## 3. Subprocess & Command Injection Defense

### Threat
An attacker manipulates parameters (URLs, format IDs, titles, filenames) to escape shell contexts and execute arbitrary commands on the backend server.

### Subprocess Safety Standard
1. **Zero Shell Execution**:
   - `shell=True` in `subprocess.Popen`, `subprocess.run`, or `os.system` is strictly prohibited throughout the entire codebase.
2. **Deterministic Argument Arrays**:
   - All invocations of external binaries (`ffmpeg`, `ffprobe`, `yt-dlp`) pass explicit argument lists `[binary_path, arg1, arg2, ...]`.
3. **Parameter Type & Regex Validation**:
   - Format selectors are strictly validated against alphanumeric tokens and known safe characters (`[a-zA-Z0-9_\-\+]+`).
   - Bitrates are constrained to an explicit enum (`320k`, `256k`, `192k`, `128k`, `64k`).
   - Image indexes are parsed strictly as unsigned integers.

---

## 4. Path Traversal & Filename Sanitization

### Threat
An attacker crafts a URL or malicious media title containing `../`, `..\`, absolute paths (`/etc/passwd`, `C:\Windows\...`), null bytes (`\0`), or special symbols to overwrite or exfiltrate arbitrary files.

### Filename Sanitization Standard
1. **Sanitization Filter**:
   - Media titles are filtered through a strict sanitizer:
     ```python
     # Remove illegal characters across Linux and Windows filesystems
     sanitized = re.sub(r'[\/\\:\*\?"<>\|\x00-\x1f]', '_', title)
     # Strip leading/trailing dots and whitespace
     sanitized = sanitized.strip('. ')
     # Prevent Windows reserved names
     if sanitized.upper() in {"CON", "PRN", "AUX", "NUL", "COM1", "COM2", "LPT1", "LPT2"}:
         sanitized = f"file_{sanitized}"
     # Enforce maximum byte length (200 bytes)
     sanitized = sanitized.encode('utf-8')[:200].decode('utf-8', 'ignore')
     ```
2. **Isolated Directory Jails**:
   - Each download job runs inside an isolated, newly created directory `/tmp/media-downloader/{job_id}/` where `{job_id}` is a verified UUIDv4.
   - All output file paths are resolved and asserted to stay within the canonical path of `job_dir` (`Path(file).resolve().is_relative_to(job_dir)`).

---

## 5. Resource Limits & Denial-of-Service (DoS) Protection

| Resource | Constraint | Enforcement Point |
| :--- | :--- | :--- |
| **Max Download File Size** | 5,000 MB (5 GB) | `yt-dlp` `max_filesize` option & streaming response length check |
| **Max Playlist Items** | 50 items | `YtDlpService` playlist extractor limit (`playlist_items: "1-50"`) |
| **Max Extraction Timeout** | 20 seconds | Socket timeout & AsyncIO `asyncio.wait_for` |
| **Max Job Execution Duration**| 900 seconds (15 min)| Worker task deadline timer |
| **Max Concurrent Jobs / IP** | 3 concurrent active jobs | Redis key tracking active job tickets per IP |
| **Rate Limit (`/api/extract`)** | 20 requests / minute | In-memory / Redis sliding-window token bucket |
| **Rate Limit (`/api/jobs`)** | 10 jobs / minute | In-memory / Redis sliding-window token bucket |
| **Temporary File Retention** | 3600 seconds (1 hour)| Automatic sweeper worker scanning every 60s |

---

## 6. Admin Authentication & Secrets Management

1. **Admin Endpoint Protection**:
   - All `/admin` API routes require a bearer token (`ADMIN_SECRET_KEY`) or session token.
   - Timing-attack-safe comparison (`hmac.compare_digest`) is enforced on token validation.
2. **Environment Variable Isolation**:
   - All operational secrets and runtime configurations are read from `.env` via Pydantic `BaseSettings`.
   - No hardcoded secrets, keys, or passwords exist in source code or Dockerfiles.
3. **Structured Log Sanitization**:
   - Log formatters explicitly mask access tokens, cookie headers, API keys, and credential parameters.

---

## 7. Content-Type & Browser Delivery Security

1. **RFC-Compliant Headers**:
   - Downloads delivered via `/api/download/{job_id}` use `Content-Disposition: attachment; filename="Sanitized_Title.ext"; filename*=UTF-8''Sanitized_Title.ext`.
2. **No Path Leaks**:
   - Server internal directory trees, temp paths, and raw system IDs are never sent in response headers or error bodies.
3. **Security Headers**:
   - `X-Content-Type-Options: nosniff`
   - `X-Frame-Options: DENY`
   - `Referrer-Policy: strict-origin-when-cross-origin`
   - `Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; media-src 'self' blob: https:; connect-src 'self' ws: wss:;`
