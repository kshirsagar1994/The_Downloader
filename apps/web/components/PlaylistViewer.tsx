"use client";

import * as React from "react";
import { ListVideo, CheckSquare, Square, Download, Clock, User, Check } from "lucide-react";
import { PlaylistItem } from "../types/media";
import { formatDuration } from "../lib/utils";

interface PlaylistViewerProps {
  items: PlaylistItem[];
  selectedIndices: number[];
  onToggleIndex: (index: number) => void;
  onSelectAll: () => void;
  onClearAll: () => void;
  onDownloadBatch: (indices: number[]) => void;
  isSubmitting: boolean;
}

export function PlaylistViewer({
  items,
  selectedIndices,
  onToggleIndex,
  onSelectAll,
  onClearAll,
  onDownloadBatch,
  isSubmitting,
}: PlaylistViewerProps) {
  const isAllSelected = items.length > 0 && selectedIndices.length === items.length;
  const hasSelection = selectedIndices.length > 0;

  return (
    <div className="space-y-4">
      {/* Playlist Controls Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 rounded-xl bg-card/40 border border-border/70">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-foreground flex items-center gap-1.5">
            <ListVideo className="w-4 h-4 text-purple-400" />
            Playlist Items ({items.length})
          </span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20 font-medium">
            {selectedIndices.length} selected
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={isAllSelected ? onClearAll : onSelectAll}
            className="px-3 py-1.5 text-xs font-medium rounded-lg border border-border bg-card hover:bg-muted text-foreground transition-colors flex items-center gap-1.5"
          >
            {isAllSelected ? (
              <>
                <Square className="w-3.5 h-3.5" />
                Deselect All
              </>
            ) : (
              <>
                <CheckSquare className="w-3.5 h-3.5" />
                Select All
              </>
            )}
          </button>

          <button
            type="button"
            disabled={!hasSelection || isSubmitting}
            onClick={() => onDownloadBatch(selectedIndices)}
            className="px-4 py-1.5 text-xs font-semibold rounded-lg bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white shadow-md shadow-purple-500/20 transition-all flex items-center gap-1.5 disabled:opacity-50"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download Batch ({selectedIndices.length})</span>
          </button>
        </div>
      </div>

      {/* Playlist List */}
      <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1">
        {items.map((item) => {
          const isSelected = selectedIndices.includes(item.index);
          return (
            <div
              key={item.id || item.index}
              onClick={() => onToggleIndex(item.index)}
              className={`p-3 rounded-xl border transition-all cursor-pointer flex items-center gap-3.5 ${
                isSelected
                  ? "border-purple-500 bg-purple-500/10 ring-1 ring-purple-500/40"
                  : "border-border/60 bg-card/40 hover:bg-card/80 hover:border-border"
              }`}
            >
              {/* Checkbox */}
              <div
                className={`w-5 h-5 rounded-md border flex items-center justify-center shrink-0 transition-all ${
                  isSelected
                    ? "bg-purple-600 border-purple-500 text-white"
                    : "border-border bg-background"
                }`}
              >
                {isSelected && <Check className="w-3.5 h-3.5 stroke-[3]" />}
              </div>

              {/* Thumbnail */}
              <div className="relative w-20 h-12 rounded-lg bg-muted/40 overflow-hidden shrink-0 border border-border/40">
                {item.thumbnail ? (
                  <img
                    src={item.thumbnail}
                    alt={item.title}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-muted-foreground">
                    <ListVideo className="w-4 h-4 opacity-40" />
                  </div>
                )}
                {item.duration && item.duration > 0 && (
                  <span className="absolute bottom-1 right-1 px-1 py-0.2 rounded bg-black/80 text-[10px] text-white font-mono">
                    {formatDuration(item.duration)}
                  </span>
                )}
              </div>

              {/* Meta */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-muted-foreground font-semibold">
                    #{item.index + 1}
                  </span>
                  <h4 className="text-xs sm:text-sm font-medium text-foreground truncate">
                    {item.title}
                  </h4>
                </div>
                {item.uploader && (
                  <div className="flex items-center gap-1 text-[11px] text-muted-foreground mt-0.5">
                    <User className="w-3 h-3 text-primary" />
                    <span>{item.uploader}</span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
