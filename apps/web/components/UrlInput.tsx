"use client";

import * as React from "react";
import { Search, Clipboard, X, Loader2, Sparkles, ArrowRight } from "lucide-react";
import { motion } from "framer-motion";

interface UrlInputProps {
  onAnalyze: (url: string) => void;
  isLoading: boolean;
  initialUrl?: string;
}

export function UrlInput({ onAnalyze, isLoading, initialUrl = "" }: UrlInputProps) {
  const [url, setUrl] = React.useState(initialUrl);
  const [isFocused, setIsFocused] = React.useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const cleanUrl = url.trim();
    if (cleanUrl) {
      onAnalyze(cleanUrl);
    }
  };

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text && (text.startsWith("http://") || text.startsWith("https://"))) {
        setUrl(text.trim());
      }
    } catch {
      // Clipboard access denied or unsupported
    }
  };

  const handleClear = () => {
    setUrl("");
  };

  return (
    <div className="w-full max-w-3xl mx-auto">
      <form onSubmit={handleSubmit} className="relative group">
        {/* Glow backdrop */}
        <div
          className={`absolute -inset-1 rounded-2xl bg-gradient-to-r from-primary/40 via-blue-500/30 to-indigo-500/40 opacity-70 blur-xl transition-all duration-500 group-hover:opacity-100 ${
            isFocused ? "opacity-100 scale-[1.01]" : ""
          }`}
        />

        {/* Outer container */}
        <div className="relative flex flex-col sm:flex-row items-center gap-2 p-2 rounded-2xl border border-border/80 bg-card/90 shadow-2xl backdrop-blur-2xl transition-all">
          {/* Input field */}
          <div className="relative flex-1 w-full flex items-center">
            <div className="pl-3.5 pr-2 text-muted-foreground">
              <Search className="w-5 h-5 text-primary" />
            </div>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              placeholder="Paste media link here (YouTube, Instagram, TikTok, Twitter, Vimeo, etc.)..."
              required
              disabled={isLoading}
              className="w-full py-3.5 px-2 bg-transparent text-sm sm:text-base text-foreground placeholder:text-muted-foreground/60 focus:outline-none disabled:opacity-60"
            />
            {url && (
              <button
                type="button"
                onClick={handleClear}
                className="p-1.5 mr-1 text-muted-foreground hover:text-foreground rounded-lg hover:bg-muted/50 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            )}
            <button
              type="button"
              onClick={handlePaste}
              title="Paste from clipboard"
              className="p-2 mr-2 text-xs font-medium text-muted-foreground hover:text-foreground bg-muted/40 hover:bg-muted rounded-lg transition-colors flex items-center gap-1.5 hidden sm:flex"
            >
              <Clipboard className="w-3.5 h-3.5" />
              Paste
            </button>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isLoading || !url.trim()}
            className="w-full sm:w-auto px-6 py-3.5 rounded-xl bg-gradient-to-r from-primary via-blue-600 to-indigo-600 text-white font-semibold text-sm sm:text-base shadow-lg shadow-primary/25 hover:shadow-primary/40 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none transition-all flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Analyzing...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>Analyze</span>
                <ArrowRight className="w-4 h-4 ml-0.5" />
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
