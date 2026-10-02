"use client";

import * as React from "react";
import { Film, Sparkles, Download, CheckCircle2 } from "lucide-react";
import { MediaFormatOption } from "../types/media";
import { formatBytes } from "../lib/utils";

interface VideoFormatSelectorProps {
  formats: MediaFormatOption[];
  selectedFormatId: string;
  onSelectFormat: (formatId: string) => void;
  onDownload: () => void;
  isSubmitting: boolean;
}

export function VideoFormatSelector({
  formats,
  selectedFormatId,
  onSelectFormat,
  onDownload,
  isSubmitting,
}: VideoFormatSelectorProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
          <Film className="w-4 h-4 text-blue-500" />
          Select Video Quality & Format
        </h3>
        <span className="text-xs text-muted-foreground">
          {formats.length} qualities available
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {formats.map((fmt) => {
          const isSelected = selectedFormatId === fmt.format_id;
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
                  <div className="flex items-center gap-1.5">
                    <span className="font-bold text-sm text-foreground">
                      {fmt.label || fmt.quality || "Standard Quality"}
                    </span>
                    {fmt.is_best && (
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30">
                        BEST
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
                  {fmt.filesize_approx ? `~${formatBytes(fmt.filesize_approx)}` : "Stream Merged"}
                </span>
              </div>
            </button>
          );
        })}
      </div>

      <div className="pt-3 flex justify-end">
        <button
          type="button"
          onClick={onDownload}
          disabled={isSubmitting || !selectedFormatId}
          className="w-full sm:w-auto px-6 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold text-sm shadow-lg shadow-blue-500/25 flex items-center justify-center gap-2 transition-all disabled:opacity-50"
        >
          <Download className="w-4 h-4" />
          <span>Download Video</span>
        </button>
      </div>
    </div>
  );
}
