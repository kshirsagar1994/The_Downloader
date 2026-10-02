# Universal Media Downloader

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)]()
[![Python](https://img.shields.io/badge/Python-3.12%20%7C%203.14-blue)]()
[![Next.js](https://img.shields.io/badge/Next.js-15%20App%20Router-black)]()
[![yt--dlp](https://img.shields.io/badge/yt--dlp-2026.8.19-red)]()
[![FFmpeg](https://img.shields.io/badge/FFmpeg-Enabled-green)]()
[![Security Audit](https://img.shields.io/badge/Security%20Audit-Passed%20(53%2F53)-success)]()

A high-performance, real Universal Media Downloader built from the ground up with **Next.js 15**, **FastAPI**, **yt-dlp**, **FFmpeg**, and **Redis**. Designed with zero synthetic mocks, real stream extraction, automatic track multiplexing, real-time SSE progress streaming, multi-layer SSRF security, and ephemeral workspace cleanup.

---

## Key Features

- 🎬 **Video Downloader**: 4K, 1440p, 1080p, 720p, 480p, 360p stream extraction, automatic separate video+audio track merging via FFmpeg.
- 🎵 **Audio Downloader**: High-fidelity audio extraction and transcoding to **MP3** (320 kbps, 256 kbps, 192 kbps, 128 kbps), **M4A**, **Opus**, and **WAV**.
- 🖼️ **Image & Gallery Downloader**: First-class image discovery, single image downloads, and multi-image selection with automated sequential naming and ZIP packaging (`01-title.jpg`, `02-title.png`).
- 📑 **Playlist & Batch Downloader**: Playlist auto-detection, selective item indexing, batch aggregation, and multi-track ZIP archive bundling.
- ⚡ **Real-Time Progress Streaming**: True Server-Sent Events (SSE) `/api/jobs/{job_id}/events` delivering live speed (MB/s), ETA, downloaded bytes, percentage, and FFmpeg transcode status.
- 🔒 **Comprehensive Security Defense**:
  - Pre-flight DNS resolution SSRF blocking (private IPv4/IPv6, cloud metadata `169.254.169.254`, container gateways).
  - Array-based subprocess execution (zero shell injection vectors).
  - Strict filename sanitization and directory traversal prevention.
  - In-memory sliding window IP rate limiting.
  - Constant-time admin token verification (`/admin`).
- 🧹 **Automatic Storage Sweeping**: Per-job isolated workspaces (`/tmp/media-downloader/{job_id}`) with scheduled time-to-live eviction and orphan cleanup.
- 🎨 **Dark-First Modern UI**: Cinematic dark SaaS theme, responsive design, clipboard auto-paste, clear format selection, and accessibility compliance.

---

## System Architecture

```
Internet / User Browser
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Nginx Reverse Proxy (:80)                 │
└──────────────┬───────────────────────────────┬──────────────┘
               │                               │
        / (Next.js SSR)                 /api/ (FastAPI)
               ▼                               ▼
┌─────────────────────────────┐ ┌─────────────────────────────┐
│    Next.js 15 Web App       │ │     FastAPI API Server      │
│     (front-end :3000)       │ │      (back-end :8000)       │
└─────────────────────────────┘ └──────────────┬──────────────┘
                                               │
                                 ┌─────────────┴─────────────┐
                                 │ SSRF Pre-flight & Val.    │
                                 │ Metadata Discovery        │
                                 │ Redis Job Queue & PubSub  │
                                 └─────────────┬─────────────┘
                                               │
                                               ▼
                                ┌─────────────────────────────┐
                                │      Redis 7 (:6379)        │
                                └──────────────┬──────────────┘
                                               │
                                               ▼
                                ┌─────────────────────────────┐
                                │  Job Worker (back-end/worker)│
                                │   ├── yt-dlp Core Engine    │
                                │   ├── FFmpeg / FFprobe      │
                                │   └── Ephemeral Workspaces  │
                                └──────────────┬──────────────┘
                                               │
                                               ▼
                                ┌─────────────────────────────┐
                                │   Isolated Storage Root     │
                                │  /tmp/media-downloader/     │
                                └─────────────────────────────┘
```

---

## Project Structure

```
media-downloader/
├── front-end/                        # Next.js 15 App Router Frontend
│   ├── app/                          # Pages: /, /admin, /faq, /privacy, /terms
│   ├── components/                   # UI & Media Components
│   ├── lib/                          # API client & utilities
│   └── types/                        # Shared TypeScript interfaces
│
├── back-end/                         # FastAPI Backend Application & Workers
│   ├── app/
│   │   ├── api/                      # Routers: /extract, /jobs, /download, /admin, /health
│   │   ├── core/                     # Config, Logging, Errors, Rate Limiting
│   │   ├── schemas/                  # Pydantic validation models
│   │   ├── security/                 # SSRF, Sanitization, Auth
│   │   ├── services/                 # yt-dlp, FFmpeg, Video, Audio, Image, Playlist
│   │   ├── storage/                  # Ephemeral workspace manager & Sweeper
│   │   └── workers/                  # Job execution worker logic
│   ├── tests/                        # Pytest test suites (98 unit/integration/security/e2e tests)
│   ├── worker/                       # Standalone daemon runners
│   │   ├── run_worker.py             # Background Redis queue worker daemon
│   │   └── run_sweeper.py            # Automated storage eviction cron
│   ├── pyproject.toml                # Python package & tool configuration
│   └── requirements.txt              # Python production dependencies
│
├── infrastructure/
│   ├── docker/                       # Dockerfiles for API, Web, Worker
│   └── nginx/                        # Nginx reverse proxy configuration
│
├── ARCHITECTURE.md                   # Complete architectural specification
├── PROJECT_PLAN.md                   # 17-Phase master roadmap
├── SECURITY.md                       # Security policies and audit report
├── docker-compose.yml                # Production multi-container composition
└── .env.example                      # Environment variable templates
```

---

## Quick Start Guide

### Prerequisites
- **Python 3.12+**
- **Node.js 20+** & **npm 10+**
- **FFmpeg & FFprobe** installed and added to your system `PATH`
- **Redis** (optional in local development — falls back gracefully to in-memory queues)

### 1. Environment Configuration
Copy the sample environment file:
```bash
cp .env.example .env
```

### 2. Backend Installation & Run
```bash
cd back-end
python -m venv .venv

# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Installation & Run
```bash
cd front-end
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

### 4. Background Worker & Storage Sweeper (Optional / Production)
```bash
# In separate terminal windows with backend venv activated:
python back-end/worker/run_worker.py
python back-end/worker/run_sweeper.py
```

---

## Docker Deployment (Recommended)

To run the full stack with Nginx, Next.js, FastAPI, Worker, and Redis in production containers:

```bash
docker compose up --build -d
```

Verify service status:
```bash
docker compose ps
curl http://localhost/api/health
```

---

## Testing & Quality Assurance

### Run All Backend Tests
```bash
pytest back-end/tests -v
```
*Executes all 98 test cases covering unit services, format selectors, transcode handlers, SSRF attack vectors, command injection boundaries, and full end-to-end pipelines.*

### Run Python Linter & Formatter
```bash
ruff check back-end/
```

### Run Frontend Production Build & Type Check
```bash
npm --prefix front-end run build
```

---

## API Endpoints Reference

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/extract` | Analyzes URL via yt-dlp and returns structured formats, streams, and galleries |
| `POST` | `/api/jobs` | Enqueues a download job and returns `job_id` |
| `GET` | `/api/jobs/{id}` | Retrieves real-time job status and progress telemetry |
| `GET` | `/api/jobs/{id}/events` | Real-time Server-Sent Events (SSE) stream for download progress |
| `POST` | `/api/jobs/{id}/cancel` | Safely halts and cancels an active job |
| `GET` | `/api/download/{id}` | Streams the completed file with proper RFC 5987 `Content-Disposition` |
| `GET` | `/api/health` | Multi-subsystem health telemetry (FastAPI, Redis, yt-dlp, FFmpeg) |
| `GET` | `/api/admin/metrics` | System telemetry, disk usage, and active job metrics (Protected) |

---

## Legal & Compliance Notice

This software is designed exclusively for downloading and converting content that you own, have authorized rights to, or is in the public domain. Universal Media Downloader does not circumvent DRM, paid subscription paywalls, or authentication systems. Users are responsible for complying with the terms of service of any third-party platform.
