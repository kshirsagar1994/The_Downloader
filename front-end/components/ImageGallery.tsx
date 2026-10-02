"use client";

import * as React from "react";
import { Image as ImageIcon, CheckSquare, Square, Download, Archive, Check } from "lucide-react";
import { MediaImageItem } from "../types/media";
import { formatBytes } from "../lib/utils";

interface ImageGalleryProps {
  images: MediaImageItem[];
  selectedIndices: number[];
  onToggleIndex: (index: number) => void;
  onSelectAll: () => void;
  onClearAll: () => void;
  onDownloadBatch: (indices: number[]) => void;
  onDownloadSingle: (index: number) => void;
  isSubmitting: boolean;
}

export function ImageGallery({
  images,
  selectedIndices,
  onToggleIndex,
  onSelectAll,
  onClearAll,
  onDownloadBatch,
  onDownloadSingle,
  isSubmitting,
}: ImageGalleryProps) {
  const isAllSelected = images.length > 0 && selectedIndices.length === images.length;
  const hasSelection = selectedIndices.length > 0;

  return (
    <div className="space-y-4">
      {/* Gallery Header Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-xl bg-card/40 border border-border/70">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-foreground flex items-center gap-1.5">
            <ImageIcon className="w-4 h-4 text-amber-400" />
            Discovered Images ({images.length})
          </span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-muted text-muted-foreground">
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
            className="px-4 py-1.5 text-xs font-semibold rounded-lg bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white shadow-md shadow-amber-500/20 transition-all flex items-center gap-1.5 disabled:opacity-50"
          >
            <Archive className="w-3.5 h-3.5" />
            <span>Download ZIP ({selectedIndices.length})</span>
          </button>
        </div>
      </div>

      {/* Images Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
        {images.map((img) => {
          const isSelected = selectedIndices.includes(img.index);
          return (
            <div
              key={img.id || img.index}
              className={`group relative rounded-xl border overflow-hidden bg-card/60 transition-all duration-200 flex flex-col ${
                isSelected
                  ? "border-amber-500 ring-2 ring-amber-500/50 shadow-lg shadow-amber-500/10"
                  : "border-border/70 hover:border-border"
              }`}
            >
              {/* Checkbox Trigger Top-Left */}
              <button
                type="button"
                onClick={() => onToggleIndex(img.index)}
                aria-label={`Select image ${img.index + 1}`}
                className="absolute top-2 left-2 z-10 w-6 h-6 rounded-md bg-black/70 backdrop-blur-md border border-white/20 flex items-center justify-center transition-all group-hover:scale-105"
              >
                {isSelected ? (
                  <Check className="w-4 h-4 text-amber-400 stroke-[3]" />
                ) : (
                  <div className="w-3 h-3 rounded-sm border border-white/40" />
                )}
              </button>

              {/* Image Preview */}
              <div
                onClick={() => onToggleIndex(img.index)}
                className="relative aspect-square w-full bg-muted/40 cursor-pointer overflow-hidden"
              >
                <img
                  src={img.preview_url || img.url}
                  alt={img.title || `Image ${img.index + 1}`}
                  loading="lazy"
                  className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                />
              </div>

              {/* Image Meta & Single Download */}
              <div className="p-2.5 bg-card/90 border-t border-border/40 flex items-center justify-between text-[11px] text-muted-foreground">
                <div className="truncate">
                  <div className="font-medium text-foreground truncate">
                    #{img.index + 1} {img.width ? `${img.width}x${img.height}` : "Image"}
                  </div>
                  <span className="uppercase font-mono text-[10px]">
                    {img.format || "JPG"} {img.filesize ? `• ${formatBytes(img.filesize)}` : ""}
                  </span>
                </div>

                <button
                  type="button"
                  title="Download this image individually"
                  disabled={isSubmitting}
                  onClick={(e) => {
                    e.stopPropagation();
                    onDownloadSingle(img.index);
                  }}
                  className="p-1.5 rounded-lg border border-border bg-background hover:bg-muted text-foreground transition-colors shrink-0"
                >
                  <Download className="w-3.5 h-3.5 text-primary" />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
