"use client";

import * as React from "react";
import { Download, Loader2, CheckCircle2, AlertCircle, XCircle, FileCheck, Sparkles, RefreshCw } from "lucide-react";
import { JobProgressEvent } from "../types/media";
import { formatBytes, formatSpeed, formatEta } from "../lib/utils";
import { API_BASE_URL } from "../lib/api";

interface DownloadProgressProps {
  job: JobProgressEvent;
  onCancel: () => void;
  onReset: () => void;
}

export function DownloadProgress({ job, onCancel, onReset }: DownloadProgressProps) {
  const isCompleted = job.status === "COMPLETED";
  const isFailed = job.status === "FAILED";
  const isCancelled = job.status === "CANCELLED";
  const isProcessing = ["QUEUED", "ANALYZING", "DOWNLOADING", "PROCESSING", "PACKAGING"].includes(
    job.status
  );

  const getStatusBadge = () => {
    switch (job.status) {
      case "QUEUED":
        return { label: "In Queue...", color: "bg-amber-500/10 text-amber-400 border-amber-500/20" };
      case "ANALYZING":
        return { label: "Resolving Streams...", color: "bg-blue-500/10 text-blue-400 border-blue-500/20" };
      case "DOWNLOADING":
        return { label: "Downloading...", color: "bg-primary/10 text-primary border-primary/20" };
      case "PROCESSING":
        return { label: "Processing Media...", color: "bg-indigo-500/10 text-indigo-400 border-indigo-500/20" };
      case "PACKAGING":
        return { label: "Packaging ZIP Archive...", color: "bg-purple-500/10 text-purple-400 border-purple-500/20" };
      case "COMPLETED":
        return { label: "Download Ready!", color: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" };
      case "FAILED":
        return { label: "Failed", color: "bg-rose-500/10 text-rose-400 border-rose-500/20" };
      case "CANCELLED":
        return { label: "Cancelled", color: "bg-muted text-muted-foreground border-border" };
      default:
        return { label: job.status, color: "bg-muted text-muted-foreground border-border" };
    }
  };

  const badge = getStatusBadge();

  // Trigger browser download by visiting or opening the endpoint
  const handleSaveToBrowser = () => {
    if (job.download_url) {
      const targetUrl = job.download_url.startsWith("http")
        ? job.download_url
        : `${API_BASE_URL}${job.download_url.startsWith("/") ? "" : "/"}${job.download_url}`;
      window.location.href = targetUrl;
    } else {
      window.location.href = `${API_BASE_URL}/api/download/${job.job_id}`;
    }
  };

  return (
    <div className="w-full rounded-2xl border border-border/80 bg-card/70 backdrop-blur-2xl p-6 sm:p-8 shadow-2xl space-y-6">
      {/* Header Info */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary">
            {isCompleted ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            ) : isFailed ? (
              <AlertCircle className="w-5 h-5 text-rose-400" />
            ) : (
              <Loader2 className="w-5 h-5 animate-spin text-primary" />
            )}
          </div>
          <div>
            <h3 className="text-base font-bold text-foreground">
              {job.filename || "Media Job Processing"}
            </h3>
            <p className="text-xs text-muted-foreground">{job.stage_message || "Working..."}</p>
          </div>
        </div>

        <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${badge.color}`}>
          {badge.label}
        </span>
      </div>

      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs font-semibold">
          <span className="text-muted-foreground">
            {isProcessing ? "Download Progress" : isCompleted ? "Ready for Save" : "Status"}
          </span>
          <span className="font-mono text-foreground text-sm">
            {Math.round(job.progress)}%
          </span>
        </div>

        {/* Outer Bar */}
        <div className="relative h-3 w-full rounded-full bg-muted/60 overflow-hidden border border-border/60">
          <div
            className={`h-full transition-all duration-300 rounded-full ${
              isCompleted
                ? "bg-gradient-to-r from-emerald-500 to-teal-400 shadow-md shadow-emerald-500/50"
                : isFailed
                ? "bg-rose-500"
                : "bg-gradient-to-r from-primary via-blue-500 to-indigo-500 shadow-md shadow-primary/50"
            }`}
            style={{ width: `${Math.min(100, Math.max(0, job.progress))}%` }}
          />
        </div>
      </div>

      {/* Metrics Row */}
      {isProcessing && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-3.5 rounded-xl bg-background/50 border border-border/60 text-xs">
          <div>
            <span className="text-muted-foreground block text-[11px]">Transferred</span>
            <span className="font-mono font-medium text-foreground">
              {formatBytes(job.downloaded_bytes)} /{" "}
              {job.total_bytes ? formatBytes(job.total_bytes) : "Unknown"}
            </span>
          </div>

          <div>
            <span className="text-muted-foreground block text-[11px]">Speed</span>
            <span className="font-mono font-medium text-foreground">
              {formatSpeed(job.speed)}
            </span>
          </div>

          <div>
            <span className="text-muted-foreground block text-[11px]">Estimated Time</span>
            <span className="font-mono font-medium text-foreground">
              {job.eta > 0 ? `ETA ${formatEta(job.eta)}` : "--:--"}
            </span>
          </div>

          <div>
            <span className="text-muted-foreground block text-[11px]">Job ID</span>
            <span className="font-mono text-[10px] text-muted-foreground truncate block">
              {job.job_id.substring(0, 8)}...
            </span>
          </div>
        </div>
      )}

      {/* Error Message display */}
      {isFailed && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs space-y-1">
          <div className="font-semibold flex items-center gap-1.5">
            <AlertCircle className="w-4 h-4" />
            {job.error_code || "DOWNLOAD_ERROR"}
          </div>
          <p className="text-rose-300/80 leading-relaxed">
            {job.error_message || "An unexpected error occurred during extraction or downloading."}
          </p>
        </div>
      )}

      {/* Actions */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
        <button
          type="button"
          onClick={onReset}
          className="px-4 py-2 text-xs font-medium text-muted-foreground hover:text-foreground rounded-lg border border-border hover:bg-muted/40 transition-colors flex items-center gap-1.5"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Download Another
        </button>

        <div className="flex items-center gap-2">
          {isProcessing && (
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 text-xs font-medium text-rose-400 hover:text-rose-300 rounded-lg border border-rose-500/20 hover:bg-rose-500/10 transition-colors flex items-center gap-1.5"
            >
              <XCircle className="w-3.5 h-3.5" />
              Cancel Job
            </button>
          )}

          {isCompleted && (
            <button
              type="button"
              onClick={handleSaveToBrowser}
              className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-semibold text-sm shadow-lg shadow-emerald-500/25 flex items-center gap-2 transition-all hover:scale-105 active:scale-95"
            >
              <Download className="w-4 h-4" />
              <span>Save File to Device</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
