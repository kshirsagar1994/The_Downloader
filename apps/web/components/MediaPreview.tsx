"use client";

import * as React from "react";
import Image from "next/image";
import { Film, Music, Image as ImageIcon, ListVideo, User, Clock, Globe } from "lucide-react";
import { ExtractionResult } from "../types/media";
import { formatDuration } from "../lib/utils";

interface MediaPreviewProps {
  media: ExtractionResult;
}

export function MediaPreview({ media }: MediaPreviewProps) {
  const [imgError, setImgError] = React.useState(false);

  const getMediaBadge = () => {
    switch (media.type) {
      case "video":
        return { label: "Video", icon: Film, color: "bg-blue-500/10 text-blue-400 border-blue-500/20" };
      case "audio":
        return { label: "Audio", icon: Music, color: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" };
      case "image":
      case "gallery":
        return { label: "Image Gallery", icon: ImageIcon, color: "bg-amber-500/10 text-amber-400 border-amber-500/20" };
      case "playlist":
        return { label: "Playlist", icon: ListVideo, color: "bg-purple-500/10 text-purple-400 border-purple-500/20" };
      default:
        return { label: "Media", icon: Film, color: "bg-primary/10 text-primary border-primary/20" };
    }
  };

  const badge = getMediaBadge();
  const Icon = badge.icon;

  return (
    <div className="w-full rounded-2xl border border-border/80 bg-card/60 backdrop-blur-xl p-4 sm:p-6 shadow-xl space-y-4">
      <div className="flex flex-col md:flex-row gap-5 items-start">
        {/* Thumbnail Preview */}
        <div className="relative w-full md:w-64 h-44 rounded-xl overflow-hidden bg-muted/40 border border-border/60 shrink-0 shadow-inner group">
          {media.thumbnail && !imgError ? (
            <img
              src={media.thumbnail}
              alt={media.title}
              onError={() => setImgError(true)}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            />
          ) : (
            <div className="w-full h-full flex flex-col items-center justify-center text-muted-foreground gap-2">
              <Icon className="w-10 h-10 opacity-40" />
              <span className="text-xs">No preview</span>
            </div>
          )}

          {/* Duration overlay */}
          {media.duration && media.duration > 0 && (
            <div className="absolute bottom-2 right-2 px-2 py-0.5 rounded-md bg-black/80 backdrop-blur-md text-white text-[11px] font-mono font-medium flex items-center gap-1">
              <Clock className="w-3 h-3 text-muted-foreground" />
              {formatDuration(media.duration)}
            </div>
          )}
        </div>

        {/* Media Details */}
        <div className="flex-1 space-y-3 min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span
              className={`px-2.5 py-1 rounded-full text-xs font-semibold border flex items-center gap-1.5 ${badge.color}`}
            >
              <Icon className="w-3.5 h-3.5" />
              {badge.label}
            </span>

            {media.platform && (
              <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-muted/50 text-muted-foreground border border-border flex items-center gap-1">
                <Globe className="w-3 h-3" />
                {media.platform}
              </span>
            )}
          </div>

          <h2 className="text-lg sm:text-xl font-bold tracking-tight text-foreground line-clamp-2 leading-snug">
            {media.title || "Untitled Media"}
          </h2>

          {/* Metadata Row */}
          <div className="flex flex-wrap items-center gap-4 text-xs text-muted-foreground pt-1">
            {media.uploader && (
              <div className="flex items-center gap-1.5">
                <User className="w-3.5 h-3.5 text-primary" />
                <span className="font-medium text-foreground/80">{media.uploader}</span>
              </div>
            )}

            {media.total_items && media.total_items > 0 && (
              <div className="flex items-center gap-1.5">
                <ListVideo className="w-3.5 h-3.5 text-purple-400" />
                <span>{media.total_items} items in batch</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
