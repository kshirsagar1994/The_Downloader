"use client";

import * as React from "react";
import { Film, Music, Image as ImageIcon, ListVideo } from "lucide-react";
import { ExtractionResult, CreateJobRequest } from "../types/media";
import { VideoFormatSelector } from "./VideoFormatSelector";
import { AudioFormatSelector } from "./AudioFormatSelector";
import { ImageGallery } from "./ImageGallery";
import { PlaylistViewer } from "./PlaylistViewer";

interface FormatSelectorProps {
  media: ExtractionResult;
  onSubmitJob: (request: CreateJobRequest) => void;
  isSubmitting: boolean;
}

export function FormatSelector({ media, onSubmitJob, isSubmitting }: FormatSelectorProps) {
  // Determine initial active tab based on extracted media type
  const [activeTab, setActiveTab] = React.useState<"video" | "audio" | "image" | "playlist">(() => {
    if (media.type === "audio") return "audio";
    if (media.type === "image" || media.type === "gallery") return "image";
    if (media.type === "playlist") return "playlist";
    return "video";
  });

  // Video State
  const defaultVideoFormat = media.video_formats.find((f) => f.is_best)?.format_id || media.video_formats[0]?.format_id || "";
  const [selectedVideoFormatId, setSelectedVideoFormatId] = React.useState<string>(defaultVideoFormat);

  // Audio State
  const [selectedAudioBitrate, setSelectedAudioBitrate] = React.useState<string>("320k");
  const [selectedAudioExt, setSelectedAudioExt] = React.useState<string>("mp3");

  // Image Gallery State
  const [selectedImageIndices, setSelectedImageIndices] = React.useState<number[]>(
    () => media.images.map((img) => img.index)
  );

  // Playlist State
  const [selectedPlaylistIndices, setSelectedPlaylistIndices] = React.useState<number[]>(
    () => media.playlist_items.map((item) => item.index)
  );

  // Handlers
  const handleVideoDownload = () => {
    onSubmitJob({
      url: media.url,
      media_type: "video",
      format_id: selectedVideoFormatId,
    });
  };

  const handleAudioDownload = () => {
    onSubmitJob({
      url: media.url,
      media_type: "audio",
      audio_bitrate: selectedAudioBitrate,
      target_extension: selectedAudioExt,
    });
  };

  const handleImageBatchDownload = (indices: number[]) => {
    onSubmitJob({
      url: media.url,
      media_type: "gallery",
      selected_image_indices: indices,
    });
  };

  const handleImageSingleDownload = (index: number) => {
    onSubmitJob({
      url: media.url,
      media_type: "image",
      selected_image_indices: [index],
    });
  };

  const handlePlaylistDownload = (indices: number[]) => {
    onSubmitJob({
      url: media.url,
      media_type: "playlist",
      selected_playlist_indices: indices,
    });
  };

  const hasVideos = media.video_formats.length > 0;
  const hasAudio = media.audio_formats.length > 0 || media.video_formats.length > 0;
  const hasImages = media.images.length > 0;
  const hasPlaylist = media.playlist_items.length > 0;

  return (
    <div className="w-full rounded-2xl border border-border/80 bg-card/60 backdrop-blur-xl p-4 sm:p-6 shadow-xl space-y-6">
      {/* Category Tabs Header */}
      <div className="flex border-b border-border/80 gap-2 pb-2 overflow-x-auto">
        {hasVideos && (
          <button
            type="button"
            onClick={() => setActiveTab("video")}
            className={`px-4 py-2.5 rounded-xl font-medium text-xs sm:text-sm flex items-center gap-2 transition-all shrink-0 ${
              activeTab === "video"
                ? "bg-primary text-white shadow-md shadow-primary/20"
                : "text-muted-foreground hover:text-foreground hover:bg-muted/40"
            }`}
          >
            <Film className="w-4 h-4" />
            <span>Video Formats</span>
          </button>
        )}

        {hasAudio && (
          <button
            type="button"
            onClick={() => setActiveTab("audio")}
            className={`px-4 py-2.5 rounded-xl font-medium text-xs sm:text-sm flex items-center gap-2 transition-all shrink-0 ${
              activeTab === "audio"
                ? "bg-emerald-600 text-white shadow-md shadow-emerald-500/20"
                : "text-muted-foreground hover:text-foreground hover:bg-muted/40"
            }`}
          >
            <Music className="w-4 h-4" />
            <span>Audio & MP3</span>
          </button>
        )}

        {hasImages && (
          <button
            type="button"
            onClick={() => setActiveTab("image")}
            className={`px-4 py-2.5 rounded-xl font-medium text-xs sm:text-sm flex items-center gap-2 transition-all shrink-0 ${
              activeTab === "image"
                ? "bg-amber-600 text-white shadow-md shadow-amber-500/20"
                : "text-muted-foreground hover:text-foreground hover:bg-muted/40"
            }`}
          >
            <ImageIcon className="w-4 h-4" />
            <span>Images & Gallery ({media.images.length})</span>
          </button>
        )}

        {hasPlaylist && (
          <button
            type="button"
            onClick={() => setActiveTab("playlist")}
            className={`px-4 py-2.5 rounded-xl font-medium text-xs sm:text-sm flex items-center gap-2 transition-all shrink-0 ${
              activeTab === "playlist"
                ? "bg-purple-600 text-white shadow-md shadow-purple-500/20"
                : "text-muted-foreground hover:text-foreground hover:bg-muted/40"
            }`}
          >
            <ListVideo className="w-4 h-4" />
            <span>Playlist ({media.playlist_items.length})</span>
          </button>
        )}
      </div>

      {/* Tab Panels */}
      <div>
        {activeTab === "video" && hasVideos && (
          <VideoFormatSelector
            formats={media.video_formats}
            selectedFormatId={selectedVideoFormatId}
            onSelectFormat={setSelectedVideoFormatId}
            onDownload={handleVideoDownload}
            isSubmitting={isSubmitting}
          />
        )}

        {activeTab === "audio" && (
          <AudioFormatSelector
            formats={media.audio_formats}
            selectedBitrate={selectedAudioBitrate}
            targetExtension={selectedAudioExt}
            onSelectBitrate={setSelectedAudioBitrate}
            onSelectExtension={setSelectedAudioExt}
            onDownload={handleAudioDownload}
            isSubmitting={isSubmitting}
          />
        )}

        {activeTab === "image" && hasImages && (
          <ImageGallery
            images={media.images}
            selectedIndices={selectedImageIndices}
            onToggleIndex={(idx) =>
              setSelectedImageIndices((prev) =>
                prev.includes(idx) ? prev.filter((i) => i !== idx) : [...prev, idx]
              )
            }
            onSelectAll={() => setSelectedImageIndices(media.images.map((i) => i.index))}
            onClearAll={() => setSelectedImageIndices([])}
            onDownloadBatch={handleImageBatchDownload}
            onDownloadSingle={handleImageSingleDownload}
            isSubmitting={isSubmitting}
          />
        )}

        {activeTab === "playlist" && hasPlaylist && (
          <PlaylistViewer
            items={media.playlist_items}
            selectedIndices={selectedPlaylistIndices}
            onToggleIndex={(idx) =>
              setSelectedPlaylistIndices((prev) =>
                prev.includes(idx) ? prev.filter((i) => i !== idx) : [...prev, idx]
              )
            }
            onSelectAll={() => setSelectedPlaylistIndices(media.playlist_items.map((i) => i.index))}
            onClearAll={() => setSelectedPlaylistIndices([])}
            onDownloadBatch={handlePlaylistDownload}
            isSubmitting={isSubmitting}
          />
        )}
      </div>
    </div>
  );
}
