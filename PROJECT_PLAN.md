# Universal Media Downloader — Master Project Plan

## Phased Execution Strategy

This project plan enforces a strict sequential 17-Phase progression (Phase 0 through Phase 16). Each phase is gated: blocking errors must be identified, tested, and resolved before progressing to the subsequent phase.

---

## Phase Matrix

| Phase | Phase Name | Objective & Deliverables | Acceptance / Exit Criteria |
| :--- | :--- | :--- | :--- |
| **0** | **Requirements & Architecture** | Architecture, Project Plan, Security specifications. | `ARCHITECTURE.md`, `PROJECT_PLAN.md`, `SECURITY.md` validated and finalized. |
| **1** | **Repository & Project Setup** | Monorepo layout (`apps/web`, `apps/api`, `apps/worker`), config, dependencies, linter/typecheck pipelines, Redis/Docker configs. | Backend and Frontend environments build, lint cleanly, and test run successfully. |
| **2** | **Frontend Foundation** | Dark-first premium SaaS layout (Hero, URL Input, Format Placeholders, Toast system, Framer Motion transitions, responsive design). | Web app renders cleanly on mobile/desktop, clipboard paste works, component state machine ready. |
| **3** | **Backend / API Foundation** | FastAPI core setup, health endpoints (`/api/health`), structured logging, Pydantic models, CORS, Rate Limiting, SSRF guard. | Health checks pass, CORS / rate limiter active, test suite verifies validation logic. |
| **4** | **yt-dlp Integration** | `YtDlpService` metadata extraction, format categorization (Video, Audio, Image), platform detection, error normalizer. | Real URL extraction returns structured schema with zero synthetic mocking. |
| **5** | **FFmpeg Integration** | `FFmpegService` binary verification, audio transcode pipeline, video+audio stream merging, thumbnail processing. | Subprocess invocations pass safety audits, media merges generate valid deliverables. |
| **6** | **Image Downloader** | Direct image fetching, multi-image gallery extraction, batch selection, streaming ZIP packaging, sanitized filenames. | Single image & batch ZIP download functional with proper MIME headers. |
| **7** | **Video Downloader** | Resolution/format selection, progressive & adaptive stream merging, best-quality auto-selection, download pipeline. | Video downloads (MP4, WebM, MKV) function end-to-end with accurate byte counts. |
| **8** | **Audio Downloader** | Audio extraction engine (MP3 320k/256k/192k/128k, M4A, Opus, WAV), ID3/cover art embedding. | Audio transcode succeeds with accurate bitrates and clean playback. |
| **9** | **Playlist / Batch Downloader**| Multi-item playlist detection, item selection list, batch queue dispatch, aggregate progress tracking. | Playlist parsing & selective batch download queues without blocking API workers. |
| **10**| **Background Jobs & Progress** | Redis worker queue, async job manager, real-time SSE stream (`/api/jobs/{job_id}/events`), cancellation, auto-cleanup. | Worker handles async jobs, SSE streams progress updates without polling, sweeper evicts expired files. |
| **11**| **Browser Download System** | Secure file delivery endpoint (`/api/download/{job_id}`), RFC-compliant `Content-Disposition`, MIME types, cross-browser compatibility. | Browser triggers native Save As dialog, no path leaks, no synthetic blobs. |
| **12**| **Security Hardening & Audit** | SSRF verification (IPv4/IPv6 private ranges, DNS rebinding, redirect traps), Command injection tests, Path traversal tests, Rate limiting stress test. | Automated security test suite executes and passes 100% of attack test cases. |
| **13**| **Admin & Monitoring** | Protected `/admin` interface, real-time worker metrics, active jobs, disk quota, yt-dlp & FFmpeg version monitor, error logs. | Admin dashboard renders live metrics securely behind authentication token. |
| **14**| **Comprehensive Testing Suite**| Unit, Integration, API, and End-to-End automated test coverage for all media types and failure scenarios. | `pytest` and frontend tests pass with complete coverage of edge cases. |
| **15**| **Docker & Deployment** | Production `Dockerfile`s, `docker-compose.yml`, reverse proxy Nginx config, health checks, resource constraints. | Multi-container stack boots cleanly and services communicate across networks. |
| **16**| **Production Audit & Handover** | Verification of all 21 production criteria (no fake data, no path leaks, cleanup, performance, legal notices). | Full production checklist signed off. |

---

## Technical File Layout

```
The_Downloader/
├── apps/
│   ├── web/                     # Next.js 15 App Router Frontend
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   ├── globals.css
│   │   │   ├── analyze/
│   │   │   ├── download/[jobId]/
│   │   │   ├── admin/
│   │   │   ├── faq/
│   │   │   ├── terms/
│   │   │   └── privacy/
│   │   ├── components/
│   │   │   ├── ui/
│   │   │   ├── Header.tsx
│   │   │   ├── Footer.tsx
│   │   │   ├── UrlInput.tsx
│   │   │   ├── MediaPreview.tsx
│   │   │   ├── FormatSelector.tsx
│   │   │   ├── ImageGallery.tsx
│   │   │   ├── PlaylistViewer.tsx
│   │   │   ├── DownloadProgress.tsx
│   │   │   └── ThemeToggle.tsx
│   │   ├── hooks/
│   │   │   ├── useJobProgress.ts
│   │   │   └── useMediaExtractor.ts
│   │   ├── lib/
│   │   │   ├── api.ts
│   │   │   └── utils.ts
│   │   ├── types/
│   │   │   └── media.ts
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   └── tailwind.config.ts
│   │
│   ├── api/                     # FastAPI Backend Application
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── api/
│   │   │   │   ├── routes_extract.py
│   │   │   │   ├── routes_jobs.py
│   │   │   │   ├── routes_download.py
│   │   │   │   ├── routes_health.py
│   │   │   │   └── routes_admin.py
│   │   │   ├── core/
│   │   │   │   ├── logging.py
│   │   │   │   ├── rate_limit.py
│   │   │   │   └── errors.py
│   │   │   ├── schemas/
│   │   │   │   ├── media.py
│   │   │   │   ├── job.py
│   │   │   │   └── health.py
│   │   │   ├── security/
│   │   │   │   ├── ssrf.py
│   │   │   │   ├── sanitization.py
│   │   │   │   └── auth.py
│   │   │   ├── services/
│   │   │   │   ├── ytdlp_service.py
│   │   │   │   ├── ffmpeg_service.py
│   │   │   │   ├── image_service.py
│   │   │   │   └── queue_service.py
│   │   │   ├── storage/
│   │   │   │   ├── workspace.py
│   │   │   │   └── cleanup.py
│   │   │   └── workers/
│   │   │       ├── job_worker.py
│   │   │       └── sweeper_worker.py
│   │   ├── tests/
│   │   └── pyproject.toml
│   │
│   └── worker/                  # Standalone Worker Runner
│       ├── run_worker.py
│       └── run_sweeper.py
│
├── infrastructure/
│   ├── docker/
│   │   ├── Dockerfile.web
│   │   ├── Dockerfile.api
│   │   └── Dockerfile.worker
│   └── nginx/
│       └── default.conf
│
├── tests/                       # End-to-End & Integration Suite
├── docker-compose.yml
├── ARCHITECTURE.md
├── PROJECT_PLAN.md
├── SECURITY.md
├── README.md
└── .env.example
```
