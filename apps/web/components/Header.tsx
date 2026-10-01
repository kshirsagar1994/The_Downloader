"use client";

import Link from "next/link";
import { DownloadCloud, Sparkles, ShieldCheck, Layers } from "lucide-react";
import { ThemeToggle } from "./ThemeToggle";

export function Header() {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/60 bg-background/80 backdrop-blur-xl transition-all">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-primary via-blue-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-primary/20 group-hover:scale-105 transition-transform duration-200">
            <DownloadCloud className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-lg tracking-tight text-foreground">
                The <span className="text-primary font-black">Downloader</span>
              </span>
              <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-primary/10 text-primary font-semibold border border-primary/20">
                PRO
              </span>
            </div>
            <p className="text-[11px] text-muted-foreground hidden sm:block">
              Universal Downloader
            </p>
          </div>
        </Link>

        {/* Navigation Links */}
        <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-muted-foreground">
          <Link
            href="/"
            className="hover:text-foreground transition-colors flex items-center gap-1.5"
          >
            <Sparkles className="w-3.5 h-3.5 text-primary" />
            Downloader
          </Link>
          <Link
            href="/faq"
            className="hover:text-foreground transition-colors flex items-center gap-1.5"
          >
            <Layers className="w-3.5 h-3.5 text-muted-foreground" />
            FAQ & Formats
          </Link>
          <Link
            href="/privacy"
            className="hover:text-foreground transition-colors flex items-center gap-1.5"
          >
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
            Privacy & Security
          </Link>
        </nav>

        {/* Actions */}
        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            Engine Online
          </div>
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
