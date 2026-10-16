"""
Build and prepare the Next.js static export for Apache/LiteSpeed Shared Hosting (cPanel, Hostinger, GoDaddy, Plesk, etc.).

Features:
1. Inlines primary CSS bundle into HTML pages to eliminate FOUC (flash of unstyled content)
   even if the hosting server has strict or misconfigured MIME types.
2. Rewrites '_next/' path references to 'assets/' across all HTML, JS, JSON, CSS, and TXT files.
   (Shared hosting Apache/LiteSpeed mod_security frequently blocks folders starting with '_').
3. Renames the '_next' directory to 'assets'.
4. Writes an optimized .htaccess file with proper MIME types, URL rewrite rules, and caching headers.
5. Archives the export into 'shared-hosting-frontend.zip' with POSIX-standard forward slashes
   so extracting in cPanel File Manager creates the correct folder structure.
"""

import glob
import os
import shutil
import zipfile

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT_DIR = os.path.join(WORKSPACE_ROOT, "front-end", "out")
ZIP_DEST = os.path.join(WORKSPACE_ROOT, "shared-hosting-frontend.zip")


def main():
    print("=" * 60)
    print("Preparing Front-End Build for Shared Hosting Deployment")
    print("=" * 60)

    if not os.path.exists(OUT_DIR):
        raise SystemExit(
            f"Error: Static export directory not found at {OUT_DIR}.\n"
            "Please run 'npm --prefix front-end run build' first."
        )

    print(f"Target static export directory: {OUT_DIR}")

    # 1. Locate primary CSS bundle
    css_files = glob.glob(os.path.join(OUT_DIR, "_next", "static", "css", "*.css"))
    if not css_files:
        css_files = glob.glob(os.path.join(OUT_DIR, "assets", "static", "css", "*.css"))

    css_content = ""
    if css_files:
        with open(css_files[0], "r", encoding="utf-8") as f:
            css_content = f.read()
        print(f"Found CSS bundle: {os.path.basename(css_files[0])} ({len(css_content)} bytes)")
    else:
        print("Notice: No CSS bundle file found to inline.")

    # 2. Inject CSS and runtime API URL meta tag directly into every HTML file
    api_url = os.environ.get("NEXT_PUBLIC_API_URL", "https://the-downloader-nlb5.onrender.com").strip().rstrip("/")
    meta_api_tag = f'<meta name="api-base-url" content="{api_url}">'
    html_count = 0
    for root, _, files in os.walk(OUT_DIR):
        for file in files:
            if file.endswith(".html"):
                filepath = os.path.join(root, file)
                with open(filepath, "r", encoding="utf-8") as f:
                    html = f.read()

                modified = False
                if "id=\"inlined-app-css\"" not in html and css_content:
                    if "</head>" in html:
                        html = html.replace(
                            "</head>",
                            f"<style id=\"inlined-app-css\">{css_content}</style></head>",
                        )
                        modified = True

                if 'name="api-base-url"' not in html:
                    if "<head>" in html:
                        html = html.replace("<head>", f"<head>\n    {meta_api_tag}")
                        modified = True
                    elif "</head>" in html:
                        html = html.replace("</head>", f"    {meta_api_tag}\n</head>")
                        modified = True

                if modified:
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(html)
                    html_count += 1

    print(f"Inlined application CSS and runtime API meta tag ({api_url}) into {html_count} HTML page(s).")

    # 3. Replace '_next/' references with 'assets/' across all build text files
    ref_count = 0
    text_extensions = (".html", ".js", ".json", ".txt", ".css", ".map")
    for root, _, files in os.walk(OUT_DIR):
        for file in files:
            if any(file.endswith(ext) for ext in text_extensions):
                filepath = os.path.join(root, file)
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                new_content = content.replace("/_next/", "/assets/").replace("_next/", "assets/")
                if new_content != content:
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    ref_count += 1

    print(f"Rewrote '_next' references to 'assets' in {ref_count} file(s).")

    # 4. Rename '_next' directory to 'assets'
    old_next_dir = os.path.join(OUT_DIR, "_next")
    new_assets_dir = os.path.join(OUT_DIR, "assets")

    if os.path.exists(old_next_dir):
        if os.path.exists(new_assets_dir):
            shutil.rmtree(new_assets_dir)
        os.rename(old_next_dir, new_assets_dir)
        print("Renamed '_next' directory to 'assets' to bypass shared hosting security filters.")
    elif os.path.exists(new_assets_dir):
        print("'assets' directory is already configured.")

    # 5. Generate production-ready .htaccess
    htaccess_path = os.path.join(OUT_DIR, ".htaccess")
    htaccess_content = """# =========================================================================
# Apache / LiteSpeed Configuration for Shared Hosting Deployment
# =========================================================================

# Ensure correct MIME types for CSS, JS, Fonts, and Media
<IfModule mod_mime.c>
  AddType text/css .css
  AddType application/javascript .js
  AddType image/svg+xml .svg
  AddType image/webp .webp
  AddType image/png .png
  AddType image/jpeg .jpg .jpeg
  AddType font/woff .woff
  AddType font/woff2 .woff2
</IfModule>

# Enable Gzip / Deflate compression for high performance
<IfModule mod_deflate.c>
  AddOutputFilterByType DEFLATE text/plain text/html text/xml text/css application/xml application/xhtml+xml application/rss+xml application/javascript application/x-javascript application/json
</IfModule>

<IfModule mod_rewrite.c>
  RewriteEngine On
  RewriteBase /

  # NEVER rewrite static assets directory or direct media files
  RewriteRule ^assets/ - [L]
  RewriteRule ^_next/ - [L]
  RewriteCond %{REQUEST_URI} \\.(css|js|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot|webp|json|txt|xml)$ [NC]
  RewriteRule ^ - [L]

  # NEVER rewrite API requests or undefined endpoints to index.html with 200 OK
  RewriteRule ^api/ - [R=404,L]
  RewriteRule ^undefined/ - [R=404,L]

  # Clean URLs: Serve .html files if matching name exists (e.g. /faq -> /faq.html)
  RewriteCond %{REQUEST_FILENAME} !-f
  RewriteCond %{REQUEST_FILENAME} !-d
  RewriteCond %{REQUEST_FILENAME}.html -f
  RewriteRule ^(.*)$ $1.html [L]

  # Serve trailing-slash index.html for folders (e.g. /faq/ -> /faq/index.html)
  RewriteCond %{REQUEST_FILENAME} -d
  RewriteCond %{REQUEST_FILENAME}/index.html -f
  RewriteRule ^(.*)$ $1/index.html [L]

  # Single Page Application (SPA) Fallback to root index.html for client-side routing
  RewriteCond %{REQUEST_FILENAME} !-f
  RewriteCond %{REQUEST_FILENAME} !-d
  RewriteRule ^.*$ /index.html [L]
</IfModule>

# Caching headers for Static Assets
<IfModule mod_expires.c>
  ExpiresActive On
  ExpiresByType text/html "access plus 0 seconds"
  ExpiresByType text/css "access plus 1 year"
  ExpiresByType application/javascript "access plus 1 year"
  ExpiresByType image/webp "access plus 1 year"
  ExpiresByType image/svg+xml "access plus 1 year"
  ExpiresByType image/png "access plus 1 year"
  ExpiresByType image/jpeg "access plus 1 year"
  ExpiresByType font/woff2 "access plus 1 year"
  ExpiresByType font/woff "access plus 1 year"
</IfModule>
"""
    with open(htaccess_path, "w", encoding="utf-8") as f:
        f.write(htaccess_content)
    print("Created production-ready .htaccess with MIME types, clean URL rewrites, and caching.")

    # 6. Create ZIP archive with POSIX forward slashes
    if os.path.exists(ZIP_DEST):
        os.remove(ZIP_DEST)

    total_files = 0
    with zipfile.ZipFile(ZIP_DEST, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(OUT_DIR):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, OUT_DIR).replace("\\", "/")
                zipf.write(full_path, rel_path)
                total_files += 1

    zip_size_kb = os.path.getsize(ZIP_DEST) / 1024
    print("=" * 60)
    print(f"SUCCESS: Package created with {total_files} files.")
    print(f"Archive: {ZIP_DEST}")
    print(f"Size:    {zip_size_kb:.1f} KB")
    print("=" * 60)


if __name__ == "__main__":
    main()
