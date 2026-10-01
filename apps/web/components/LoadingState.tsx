"use client";

import * as React from "react";
import { Loader2, Sparkles, Layers, ShieldCheck } from "lucide-react";

interface LoadingStateProps {
  message?: string;
  subMessage?: string;
}

export function LoadingState({
  message = "Inspecting media streams & formats...",
  subMessage = "Querying yt-dlp metadata engine and validating stream sources safely",
}: LoadingStateProps) {
  return (
    <div className="w-full max-w-2xl mx-auto rounded-2xl border border-border/80 bg-card/60 backdrop-blur-xl p-8 text-center space-y-6 shadow-2xl">
      <div className="relative w-16 h-16 mx-auto">
        <div className="absolute inset-0 rounded-2xl bg-primary/20 blur-xl animate-pulse" />
        <div className="relative w-16 h-16 rounded-2xl bg-gradient-to-tr from-primary via-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-primary/30">
          <Loader2 className="w-8 h-8 animate-spin" />
        </div>
      </div>

      <div className="space-y-2">
        <h3 className="text-lg font-bold text-foreground flex items-center justify-center gap-2">
          <Sparkles className="w-4 h-4 text-primary" />
          {message}
        </h3>
        <p className="text-xs text-muted-foreground max-w-md mx-auto leading-relaxed">
          {subMessage}
        </p>
      </div>

      {/* Shimmer Placeholder cards */}
      <div className="space-y-3 pt-2">
        <div className="h-14 w-full rounded-xl bg-muted/40 animate-pulse" />
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          <div className="h-16 rounded-xl bg-muted/30 animate-pulse" />
          <div className="h-16 rounded-xl bg-muted/30 animate-pulse" />
          <div className="h-16 rounded-xl bg-muted/30 animate-pulse hidden sm:block" />
        </div>
      </div>
    </div>
  );
}
