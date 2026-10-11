"use client";

import * as React from "react";
import { Film, Sparkles, Download, CheckCircle2, Globe, AlertTriangle, ExternalLink } from "lucide-react";
import { MediaFormatOption } from "../types/media";
import { formatBytes } from "../lib/utils";
import { downloadDirect, getDownloadableFormats, formatFileSize } from "../lib/download";

interface VideoFormatSelectorProps {
  formats: MediaFormatOption[];
  selectedFormatId: string;
  onSelectFormat: (formatId: string) => void;
  onDownload: () => void;
  isSubmitting: boolean;
  // Optional props for direct download
  mediaUrl?: string;
  mediaTitle?: string;
  onDirectDownload?: (format: MediaFormatOption) => Promise<void>;
  directDownloadStatus?: { formatId: string; status: 'idle' | 'downloading' | 'success' | 'error'; message: string } | null;
}

export function VideoFormatSelector({
  formats,
  selectedFormatId,
  onSelectFormat,
  onDownload,
  isSubmitting,
  mediaUrl,
  mediaTitle,
  onDirectDownload,
  directDownloadStatus,
}: VideoFormatSelectorProps) {
  const [showDirectDownloadInfo, setShowDirectDownloadInfo] = React.useState(false);
  const [internalStatus, setInternalStatus] = React.useState<{
    formatId: string;
    status: 'idle' | 'downloading' | 'success' | 'error';
    message: string;
  } | null>(null);

  const activeStatus = directDownloadStatus ?? internalStatus;
  
  const downloadable = getDownloadableFormats(formats);
  const hasDirectDownload = downloadable.progressive.length > 0;

  const handleDirectDownload = async (format: MediaFormatOption) => {
    if (onDirectDownload) {
      await onDirectDownload(format);
      return;
    }

    if (!format.url) return;

    setInternalStatus({ formatId: format.format_id, status: 'downloading', message: 'Downloading...' });
    try {
      const res = await downloadDirect({
        format: {
          format_id: format.format_id,
          label: format.label || format.quality || 'video',
          extension: format.extension || 'mp4',
          url: format.url,
          video_url: format.video_url,
          audio_url: format.audio_url,
          manifest_url: format.manifest_url,
          protocol: format.protocol,
          has_video: Boolean(format.has_video),
          has_audio: Boolean(format.has_audio),
        },
        title: mediaTitle || 'video',
        onComplete: () => {
          setInternalStatus({ formatId: format.format_id, status: 'success', message: 'Download started' });
        },
        onError: (err) => {
          setInternalStatus({ formatId: format.format_id, status: 'error', message: err });
        },
      });
      if (res.success) {
        setInternalStatus({ formatId: format.format_id, status: 'success', message: res.message });
      } else {
        setInternalStatus({ formatId: format.format_id, status: 'error', message: res.message });
      }
    } catch (e: any) {
      setInternalStatus({ formatId: format.format_id, status: 'error', message: e?.message || 'Download failed' });
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
          <Film className="w-4 h-4 text-blue-500" />
          Select Video Quality & Format
        </h3>
        <div className="flex items-center gap-2">
          {hasDirectDownload && (
            <button
              type="button"
              onClick={() => setShowDirectDownloadInfo(!showDirectDownloadInfo)}
              className="px-2 py-1 text-xs text-muted-foreground hover:text-foreground flex items-center gap-1 rounded"
            >
              <Globe className="w-3 h-3" />
              <span>Direct Download</span>
            </button>
          )}
          <span className="text-xs text-muted-foreground">
            {formats.length} qualities available
          </span>
        </div>
      </div>

      {hasDirectDownload && showDirectDownloadInfo && (
        <div className="p-3 rounded-lg bg-green-500/10 border border-green-500/20 text-green-400 text-sm flex items-start gap-2">
          <Sparkles className="w-4 h-4 mt-0.5 shrink-0" />
          <div>
            <strong>Direct Browser Download Available</strong>
            <p className="mt-1 opacity-90">
              These formats download directly from YouTube to your browser using your IP and cookies.
              No server-side bot verification needed!
            </p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {formats.map((fmt) => {
          const isSelected = selectedFormatId === fmt.format_id;
          const isDirectDownloadable = fmt.url && fmt.has_video && fmt.has_audio;
          const isDownloading = activeStatus?.formatId === fmt.format_id && activeStatus.status === 'downloading';
          const downloadSuccess = activeStatus?.formatId === fmt.format_id && activeStatus.status === 'success';
          const downloadError = activeStatus?.formatId === fmt.format_id && activeStatus.status === 'error';

          return (
            <button
              key={fmt.format_id}
              type="button"
              onClick={() => onSelectFormat(fmt.format_id)}
              className={`relative p-3.5 rounded-xl border text-left transition-all duration-200 flex flex-col justify-between gap-2 group ${
                isSelected
                  ? "border-primary bg-primary/10 shadow-lg shadow-primary/10 ring-1 ring-primary"
                  : "border-border/70 bg-card/40 hover:bg-card/80 hover:border-border"
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="font-bold text-sm text-foreground">
                      {fmt.label || fmt.quality || "Standard Quality"}
                    </span>
                    {fmt.is_best && (
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30">
                        BEST
                      </span>
                    )}
                    {isDirectDownloadable && !fmt.is_best && (
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-green-500/20 text-green-400 border border-green-500/30 flex items-center gap-1">
                        <Globe className="w-2.5 h-2.5" />
                        Direct
                      </span>
                    )}
                  </div>
                  <span className="text-xs text-muted-foreground uppercase font-mono font-medium">
                    {fmt.extension || "mp4"}
                  </span>
                </div>

                {isSelected ? (
                  <CheckCircle2 className="w-4 h-4 text-primary shrink-0" />
                ) : (
                  <div className="w-4 h-4 rounded-full border border-border group-hover:border-muted-foreground shrink-0" />
                )}
              </div>

              <div className="flex items-center justify-between text-xs text-muted-foreground pt-1 border-t border-border/40">
                <span>{fmt.resolution || "Adaptive"}</span>
                <span>
                  {fmt.filesize_approx ? `~${formatBytes(fmt.filesize_approx)}` : isDirectDownloadable ? "Ready" : "Stream Merged"}
                </span>
              </div>

              {/* Direct download button per format */}
              {isDirectDownloadable && !isSubmitting && (
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDirectDownload(fmt);
                  }}
                  disabled={isDownloading || downloadSuccess}
                  className={`w-full mt-2 px-3 py-2 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition-all ${
                    isDownloading
                      ? "bg-blue-500/20 text-blue-400 cursor-wait"
                      : downloadSuccess
                      ? "bg-green-500/20 text-green-400 cursor-default"
                      : "bg-green-600 hover:bg-green-500 text-white"
                  }`}
                >
                  {isDownloading && (
                    <>
                      <svg className="animate-spin h-3 w-3" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/></svg>
                      Downloading...
                    </>
                  )}
                  {downloadSuccess && (
                    <>
                      <CheckCircle2 className="w-3 h-3" />
                      Started
                    </>
                  )}
                  {!isDownloading && !downloadSuccess && (
                    <>
                      <Download className="w-3 h-3" />
                      Direct Download
                    </>
                  )}
                </button>
              )}
              
              {downloadError && (
                <div className="mt-2 p-2 text-xs text-red-400 bg-red-500/10 rounded flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3" />
                  <span>{activeStatus?.message}</span>
                </div>
              )}
            </button>
          );
        })}
      </div>

      <div className="pt-3 flex flex-col sm:flex-row gap-3 justify-end">
        {/* Server-side download (existing) */}
        <button
          type="button"
          onClick={onDownload}
          disabled={isSubmitting || !selectedFormatId}
          className="w-full sm:w-auto px-6 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold text-sm shadow-lg shadow-blue-500/25 flex items-center justify-center gap-2 transition-all disabled:opacity-50"
        >
          <Download className="w-4 h-4" />
          <span>Download via Server</span>
        </button>

        {/* Direct download for Best quality if progressive */}
        {hasDirectDownload && (
          <button
            type="button"
            onClick={() => {
              const bestFormat = formats.find(f => f.is_best && f.url && f.has_video && f.has_audio) || 
                                downloadable.progressive[0];
              if (bestFormat) handleDirectDownload(bestFormat);
            }}
            disabled={isSubmitting || activeStatus?.status === 'downloading'}
            className="w-full sm:w-auto px-6 py-3 rounded-xl bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 text-white font-semibold text-sm shadow-lg shadow-green-500/25 flex items-center justify-center gap-2 transition-all disabled:opacity-50"
          >
            <Globe className="w-4 h-4" />
            <span>Direct Download (Best)</span>
          </button>
        )}
      </div>
    </div>
  );
}
