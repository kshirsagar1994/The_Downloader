import Link from "next/link";
import { DownloadCloud, Shield, Heart, Github } from "lucide-react";

export function Footer() {
  return (
    <footer className="w-full border-t border-border/60 bg-card/40 backdrop-blur-md mt-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-12">
          {/* Col 1: Brand Info */}
          <div className="md:col-span-1 space-y-3">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center text-primary">
                <DownloadCloud className="w-4 h-4" />
              </div>
              <span className="font-bold text-base tracking-tight">The Downloader</span>
            </div>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Real high-performance universal media downloader and converter.
            </p>
          </div>

          {/* Col 2: Supported Formats */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-foreground">
              Media Categories
            </h4>
            <ul className="space-y-2 text-xs text-muted-foreground">
              <li>Video (4K, 1440p, 1080p, 720p MP4/WebM)</li>
              <li>Audio (320kbps MP3, M4A, Opus, WAV)</li>
              <li>Images & Galleries (Single & ZIP Archive)</li>
              <li>Playlists & Batch Processing</li>
            </ul>
          </div>

          {/* Col 3: Legal & Trust */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-foreground">
              Legal & Trust
            </h4>
            <ul className="space-y-2 text-xs text-muted-foreground">
              <li>
                <Link href="/privacy" className="hover:text-foreground transition-colors">
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link href="/terms" className="hover:text-foreground transition-colors">
                  Terms of Service & Acceptable Use
                </Link>
              </li>
              <li>
                <Link href="/notices" className="hover:text-foreground transition-colors">
                  Third-Party Notices
                </Link>
              </li>
              <li>
                <Link href="/faq" className="hover:text-foreground transition-colors">
                  Security & FAQ
                </Link>
              </li>
            </ul>
          </div>

          {/* Col 4: Service Highlights */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-foreground">
              Service Highlights
            </h4>
            <div className="p-3 rounded-xl bg-background/60 border border-border/80 text-xs space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Performance:</span>
                <span className="text-primary font-medium">Ultra Fast</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Media Quality:</span>
                <span className="text-foreground font-medium">Lossless HD</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Privacy Protection:</span>
                <span className="text-emerald-400 font-medium">Zero Storage Logs</span>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-8 border-t border-border/40 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-muted-foreground">
          <p>
            &copy; 2026 Kshirsagar. All rights reserved. For authorized media downloads only.
          </p>
          <div className="flex items-center gap-4">
            <Link href="/terms" className="hover:text-foreground transition-colors">Terms</Link>
            <span>&middot;</span>
            <Link href="/privacy" className="hover:text-foreground transition-colors">Privacy</Link>
            <span>&middot;</span>
            <Link href="/notices" className="hover:text-foreground transition-colors">Third-Party Notices</Link>
            <span>&middot;</span>
            <span className="flex items-center gap-1.5">
              <Shield className="w-3.5 h-3.5 text-emerald-400 inline" /> Privacy First
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
}
