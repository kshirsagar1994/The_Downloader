import asyncio
import zipfile
from pathlib import Path

import httpx

from app.config import get_settings
from app.core.errors import DownloaderException, ProcessingFailedError
from app.core.logging import logger
from app.schemas.media import MediaImageItem
from app.security.sanitization import sanitize_extension, sanitize_filename
from app.security.ssrf import validate_url_ssrf

settings = get_settings()

MIME_TO_EXT = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
    "image/avif": "avif",
    "image/svg+xml": "svg",
}


class ImageService:
    """Handles high-speed image fetching, gallery packaging, and ZIP creation."""

    @classmethod
    async def download_single_image(
        cls,
        url: str,
        job_dir: Path,
        custom_name: str | None = None,
    ) -> Path:
        """Downloads a single image and saves it to the isolated job directory."""
        validated_url = validate_url_ssrf(url)
        job_dir.mkdir(parents=True, exist_ok=True)

        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            resp = await client.get(validated_url)
            if resp.status_code != 200:
                raise DownloaderException(
                    f"Failed to download image: HTTP {resp.status_code}",
                    code="IMAGE_DOWNLOAD_FAILED",
                )

            # Determine extension from Content-Type header or URL
            content_type = resp.headers.get("content-type", "").split(";")[0].strip().lower()
            ext = MIME_TO_EXT.get(content_type)
            if not ext:
                ext = sanitize_extension(Path(validated_url.split("?")[0]).suffix, "jpg")

            base_name = sanitize_filename(custom_name or "image")
            output_file = job_dir / f"{base_name}.{ext}"

            # Write image bytes
            output_file.write_bytes(resp.content)
            logger.info(f"Downloaded single image ({len(resp.content)} bytes) -> {output_file.name}")
            return output_file

    @classmethod
    async def download_image_gallery(
        cls,
        images: list[MediaImageItem],
        job_dir: Path,
        zip_name: str = "images.zip",
        selected_indices: list[int] | None = None,
    ) -> Path:
        """
        Concurrently downloads multiple images from a gallery or post and bundles them into a ZIP.
        Internal files are cleanly named (e.g. 01-image.jpg, 02-image.png).
        """
        job_dir.mkdir(parents=True, exist_ok=True)
        safe_zip_name = sanitize_filename(zip_name.replace(".zip", "")) + ".zip"
        zip_path = job_dir / safe_zip_name

        # Filter items if selection provided
        target_images = images
        if selected_indices is not None and len(selected_indices) > 0:
            target_images = [img for img in images if img.index in selected_indices]

        if not target_images:
            raise ProcessingFailedError("No images selected for gallery download.")

        temp_image_files: list[tuple[Path, str]] = []

        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            # Download concurrently with semaphore limit
            semaphore = asyncio.Semaphore(5)

            async def fetch_item(img: MediaImageItem, seq: int) -> None:
                async with semaphore:
                    try:
                        validated_url = validate_url_ssrf(img.url)
                        resp = await client.get(validated_url)
                        if resp.status_code == 200:
                            content_type = resp.headers.get("content-type", "").split(";")[0].strip().lower()
                            ext = MIME_TO_EXT.get(content_type) or sanitize_extension(img.format or "jpg")

                            clean_title = sanitize_filename(img.title or f"image_{seq:02d}")
                            archive_entry_name = f"{seq:02d}-{clean_title}.{ext}"

                            file_on_disk = job_dir / f"tmp_{seq:02d}.{ext}"
                            file_on_disk.write_bytes(resp.content)
                            temp_image_files.append((file_on_disk, archive_entry_name))
                    except (httpx.HTTPError, OSError, DownloaderException) as exc:
                        logger.error(f"Failed to fetch gallery image index {img.index}: {exc}")

            tasks = [fetch_item(img, i + 1) for i, img in enumerate(target_images)]
            await asyncio.gather(*tasks)

        if not temp_image_files:
            raise ProcessingFailedError("Failed to download any images from the requested gallery.")

        # Create ZIP archive
        logger.info(f"Creating ZIP archive with {len(temp_image_files)} images -> {zip_path.name}")
        with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as archive:
            for disk_file, entry_name in temp_image_files:
                archive.write(str(disk_file), arcname=entry_name)
                # Cleanup temp file on disk
                disk_file.unlink(missing_ok=True)

        return zip_path
