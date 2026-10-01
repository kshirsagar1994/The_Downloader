"use client";

import * as React from "react";
import { Music, Sparkles, Download, CheckCircle2 } from "lucide-react";
import { MediaFormatOption } from "../types/media";

interface AudioFormatSelectorProps {
  formats: MediaFormatOption[];
  selectedBitrate: string;
  targetExtension: string;
  onSelectBitrate: (bitrate: string) => void;
  onSelectExtension: (ext: string) => void;
  onDownload: () => void;
  isSubmitting: boolean;
}

const AUDIO_FORMATS = [
  { ext: "mp3", label: "MP3", desc: "Universal compatibility" },
  { ext: "m4a", label: "M4A (AAC)", desc: "Apple & modern devices" },
  { ext: "opus", label: "Opus", desc: "High-efficiency streaming" },
  { ext: "wav", label: "WAV", desc: "Uncompressed lossless master" },
];

const BITRATES = [
  { value: "320k", label: "320 kbps", quality: "Extreme / Studio Quality" },
  { value: "256k", label: "256 kbps", quality: "High Quality (Recommended)" },
  { value: "192k", label: "192 kbps", quality: "Standard Quality" },
  { value: "128k", label: "128 kbps", quality: "Compact File Size" },
];

export function AudioFormatSelector({
  selectedBitrate,
  targetExtension,
  onSelectBitrate,
  onSelectExtension,
  onDownload,
  isSubmitting,
}: AudioFormatSelectorProps) {
  return (
    <div className="space-y-6">
      {/* Target Container Extension */}
      <div className="space-y-3">
        <label className="text-sm font-semibold text-foreground flex items-center gap-2">
          <Music className="w-4 h-4 text-emerald-400" />
          1. Choose Audio Format
        </label>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {AUDIO_FORMATS.map((f) => {
            const isSelected = targetExtension === f.ext;
            return (
              <button
                key={f.ext}
                type="button"
                onClick={() => onSelectExtension(f.ext)}
                className={`p-3 rounded-xl border text-left transition-all ${
                  isSelected
                    ? "border-emerald-500 bg-emerald-500/10 shadow-lg shadow-emerald-500/10 ring-1 ring-emerald-500"
                    : "border-border/70 bg-card/40 hover:bg-card/80 hover:border-border"
                }`}
              >
                <div className="font-bold text-sm text-foreground">{f.label}</div>
                <div className="text-[11px] text-muted-foreground">{f.desc}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Bitrate Selection */}
      <div className="space-y-3">
        <label className="text-sm font-semibold text-foreground">
          2. Select Audio Bitrate
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {BITRATES.map((b) => {
            const isSelected = selectedBitrate === b.value;
            return (
              <button
                key={b.value}
                type="button"
                onClick={() => onSelectBitrate(b.value)}
                className={`p-3.5 rounded-xl border text-left transition-all flex items-center justify-between ${
                  isSelected
                    ? "border-emerald-500 bg-emerald-500/10 shadow-lg shadow-emerald-500/10 ring-1 ring-emerald-500"
                    : "border-border/70 bg-card/40 hover:bg-card/80 hover:border-border"
                }`}
              >
                <div>
                  <div className="font-bold text-sm text-foreground">{b.label}</div>
                  <div className="text-xs text-muted-foreground">{b.quality}</div>
                </div>
                {isSelected && <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />}
              </button>
            );
          })}
        </div>
      </div>

      <div className="pt-2 flex justify-end">
        <button
          type="button"
          onClick={onDownload}
          disabled={isSubmitting}
          className="w-full sm:w-auto px-6 py-3 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-semibold text-sm shadow-lg shadow-emerald-500/25 flex items-center justify-center gap-2 transition-all disabled:opacity-50"
        >
          <Download className="w-4 h-4" />
          <span>Extract & Download Audio ({targetExtension.toUpperCase()})</span>
        </button>
      </div>
    </div>
  );
}
