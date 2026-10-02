# The_Downloader — Third-Party Notices
Copyright (c) 2026 Kshirsagar

The_Downloader uses third-party open-source software and libraries.
The licenses of those third-party components remain applicable to the respective components. Nothing in The_Downloader's proprietary license is intended to override or restrict rights granted by an applicable third-party license.

---

## 1. yt-dlp
* **Project**: yt-dlp
* **Repository**: [https://github.com/yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp)
* **License**: The Unlicense

The yt-dlp project is licensed under The Unlicense. The official yt-dlp documentation states that the Git repository, PyPI source distribution, and PyPI wheel contain code licensed under The Unlicense.
The_Downloader uses yt-dlp as a third-party dependency via pip.
The standalone PyInstaller-bundled yt-dlp executables may contain additional third-party components under different licenses. The_Downloader does not bundle standalone executables.

* **Official license**: [https://github.com/yt-dlp/yt-dlp/blob/master/LICENSE](https://github.com/yt-dlp/yt-dlp/blob/master/LICENSE)
* **Official third-party notices**: [https://github.com/yt-dlp/yt-dlp/blob/master/THIRD_PARTY_LICENSES.txt](https://github.com/yt-dlp/yt-dlp/blob/master/THIRD_PARTY_LICENSES.txt)

---

## 2. FFmpeg
* **Project**: FFmpeg
* **Repository**: [https://github.com/FFmpeg/FFmpeg](https://github.com/FFmpeg/FFmpeg)
* **Website**: [https://ffmpeg.org/](https://ffmpeg.org/)
* **License**: Most FFmpeg files are licensed under the GNU Lesser General Public License version 2.1 or later (LGPL v2.1+). FFmpeg also contains optional components licensed under the GNU General Public License version 2 or later (GPL v2+). The applicable license of an FFmpeg binary depends on the build configuration and included external libraries.

The_Downloader uses FFmpeg as a third-party media-processing component via subprocess execution. The exact FFmpeg version and build used in a deployment should be recorded by the deployment operator.

* **FFmpeg official license information**: [https://ffmpeg.org/doxygen/trunk/md_LICENSE.html](https://ffmpeg.org/doxygen/trunk/md_LICENSE.html)
* **FFmpeg legal information**: [https://ffmpeg.org/legal.html](https://ffmpeg.org/legal.html)

**IMPORTANT**:
The_Downloader does not claim ownership of FFmpeg. The license applicable to the exact FFmpeg binary distributed or deployed with a particular version of The_Downloader remains applicable. If an FFmpeg build contains GPL components, the applicable GPL requirements must be followed for that build.

---

## 3. Redis
* **Project**: Redis
* **Repository**: [https://github.com/redis/redis](https://github.com/redis/redis)
* **Website**: [https://redis.io/](https://redis.io/)
* **Targeted Version**: Redis 7.2.x (Pinned `redis:7.2.16-alpine`)
* **License**: BSD 3-Clause License

Redis officially states that Redis 7.2.x and earlier remain licensed under the BSD 3-Clause license. The_Downloader uses Redis as an infrastructure component for application data, caching, and background-job coordination.

* **Official Redis license information**: [https://redis.io/legal/licenses/](https://redis.io/legal/licenses/)

**IMPORTANT**:
Redis licensing changed beginning with Redis 7.4. The deployment configuration explicitly pins Redis to `7.2.16-alpine` to maintain the BSD-3-Clause licensing model.

---

## 4. Python
* **Project**: Python
* **License**: Python Software Foundation License 2.0
* **Website**: [https://www.python.org/](https://www.python.org/)

Python is used as part of the backend runtime. The Python runtime and its third-party components maintain separate license notices.

---

## 5. Node.js
* **Project**: Node.js
* **License**: MIT License and applicable third-party notices
* **Website**: [https://nodejs.org/](https://nodejs.org/)

Node.js is used by the frontend build and runtime environment.

---

## 6. Next.js
* **Project**: Next.js
* **License**: MIT
* **Repository**: [https://github.com/vercel/next.js](https://github.com/vercel/next.js)

Next.js is used for the web application frontend.

---

## 7. React
* **Project**: React
* **License**: MIT
* **Repository**: [https://github.com/facebook/react](https://github.com/facebook/react)

React is used for the web application user interface.

---

## 8. FastAPI
* **Project**: FastAPI
* **License**: MIT
* **Repository**: [https://github.com/fastapi/fastapi](https://github.com/fastapi/fastapi)

FastAPI is used as the backend API framework.

---

## 9. Uvicorn
* **Project**: Uvicorn
* **License**: BSD 3-Clause
* **Repository**: [https://github.com/encode/uvicorn](https://github.com/encode/uvicorn)

Uvicorn is used as the ASGI server.

---

## 10. Pydantic
* **Project**: Pydantic
* **License**: MIT
* **Repository**: [https://github.com/pydantic/pydantic](https://github.com/pydantic/pydantic)

Pydantic is used for data validation and application models.

---

## 11. Redis Python Client
* **Project**: redis-py
* **License**: MIT
* **Repository**: [https://github.com/redis/redis-py](https://github.com/redis/redis-py)

redis-py is used to communicate with the Redis server.

---

## 12. Framer Motion
* **Project**: Motion / Framer Motion
* **License**: MIT
* **Repository**: [https://github.com/motiondivision/motion](https://github.com/motiondivision/motion)

Used for frontend animation and interaction.

---

## 13. Radix UI
* **Project**: Radix UI
* **License**: MIT
* **Repository**: [https://github.com/radix-ui/primitives](https://github.com/radix-ui/primitives)

Radix UI components are used by the frontend.

---

## 14. Tailwind CSS
* **Project**: Tailwind CSS
* **License**: MIT
* **Repository**: [https://github.com/tailwindlabs/tailwindcss](https://github.com/tailwindlabs/tailwindcss)

Tailwind CSS is used for frontend styling.

---

## 15. Lucide
* **Project**: Lucide
* **License**: ISC
* **Repository**: [https://github.com/lucide-icons/lucide](https://github.com/lucide-icons/lucide)

Lucide icons are used across the frontend.

---

## 16. Other Dependencies
The_Downloader includes direct and transitive dependencies installed through Python package managers, npm, Docker base images, and operating-system packages. Each dependency remains subject to its applicable license. Dependency manifests (`requirements.txt`, `package.json`, `package-lock.json`) serve as the authoritative record.

---

## 17. License Compliance
The_Downloader does not modify or replace the licenses of third-party software. Where applicable, users distributing third-party components should preserve the required copyright notices, license texts, disclaimers, and other notices required by the respective licenses.

---

## 18. No Endorsement
Use of third-party software does not imply endorsement of The_Downloader by the respective third-party project or its maintainers. The_Downloader is an independent project and is not affiliated with, sponsored by, or endorsed by yt-dlp, FFmpeg, Redis, or other third-party projects.

Last reviewed: 2026
Copyright (c) 2026 Kshirsagar
