"use client";

import * as React from "react";
import { AlertTriangle, RefreshCcw, ShieldAlert, ArrowLeft } from "lucide-react";

interface ErrorStateProps {
  title?: string;
  message: string;
  code?: string;
  onRetry?: () => void;
  onReset?: () => void;
}

export function ErrorState({
  title = "Extraction Error",
  message,
  code,
  onRetry,
  onReset,
}: ErrorStateProps) {
  return (
    <div className="w-full max-w-2xl mx-auto rounded-2xl border border-rose-500/30 bg-rose-500/5 backdrop-blur-xl p-6 sm:p-8 text-center space-y-4 shadow-xl">
      <div className="w-12 h-12 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-400 mx-auto flex items-center justify-center">
        <AlertTriangle className="w-6 h-6" />
      </div>

      <div className="space-y-1.5">
        <h3 className="text-base sm:text-lg font-bold text-foreground">{title}</h3>
        {code && (
          <span className="inline-block px-2.5 py-0.5 rounded-full bg-rose-500/10 text-rose-400 text-xs font-mono font-medium border border-rose-500/20">
            {code}
          </span>
        )}
        <p className="text-sm text-muted-foreground max-w-md mx-auto leading-relaxed">
          {message}
        </p>
      </div>

      <div className="pt-2 flex flex-wrap items-center justify-center gap-3">
        {onReset && (
          <button
            type="button"
            onClick={onReset}
            className="px-4 py-2 text-xs font-medium text-muted-foreground hover:text-foreground rounded-xl border border-border bg-card hover:bg-muted transition-colors flex items-center gap-1.5"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Try Another Link
          </button>
        )}

        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="px-4 py-2 text-xs font-semibold text-white rounded-xl bg-primary hover:bg-primary/90 transition-colors shadow-md shadow-primary/20 flex items-center gap-1.5"
          >
            <RefreshCcw className="w-3.5 h-3.5" />
            Retry Analysis
          </button>
        )}
      </div>
    </div>
  );
}
