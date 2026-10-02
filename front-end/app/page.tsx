"use client";

import * as React from "react";
import { Header } from "../components/Header";
import { Footer } from "../components/Footer";
import { UrlInput } from "../components/UrlInput";
import { MediaPreview } from "../components/MediaPreview";
import { FormatSelector } from "../components/FormatSelector";
import { DownloadProgress } from "../components/DownloadProgress";
import { LoadingState } from "../components/LoadingState";
import { ErrorState } from "../components/ErrorState";
import { ToastProvider, useToast } from "../components/Toast";
import { ExtractionResult, CreateJobRequest, JobProgressEvent } from "../types/media";
import {
  Sparkles,
  Zap,
  ShieldCheck,
  Film,
  Music,
  Image as ImageIcon,
  ListVideo,
  Lock,
  HardDrive,
  Cpu,
} from "lucide-react";

import { extractMedia, createJob, cancelJob, ApiError, API_BASE_URL } from "../lib/api";

function DownloaderApp() {
  const { showToast } = useToast();

  const [currentUrl, setCurrentUrl] = React.useState<string>("");
  const [isLoading, setIsLoading] = React.useState<boolean>(false);
  const [errorInfo, setErrorInfo] = React.useState<{ title: string; message: string; code?: string } | null>(null);
  const [extractedMedia, setExtractedMedia] = React.useState<ExtractionResult | null>(null);
  const [activeJob, setActiveJob] = React.useState<JobProgressEvent | null>(null);

  // Analyze Handler
  const handleAnalyze = async (url: string) => {
    setCurrentUrl(url);
    setIsLoading(true);
    setErrorInfo(null);
    setExtractedMedia(null);
    setActiveJob(null);

    try {
      const media = await extractMedia(url);
      setExtractedMedia(media);
      showToast("Media Extracted", `Discovered streams for "${media.title}"`, "success");
    } catch (err: any) {
      const code = err instanceof ApiError ? err.code : "EXTRACTION_FAILED";
      const message = err.message || "Could not analyze this URL. Please verify the URL is public and supported.";
      setErrorInfo({
        title: "Extraction Error",
        message,
        code,
      });
      showToast("Extraction Failed", message, "error");
    } finally {
      setIsLoading(false);
    }
  };

  // Submit Download Job Handler
  const handleSubmitJob = async (request: CreateJobRequest) => {
    setIsLoading(true);
    try {
      const { job_id } = await createJob(request);

      const initialJob: JobProgressEvent = {
        job_id,
        status: "QUEUED",
        progress: 0,
        downloaded_bytes: 0,
        total_bytes: 0,
        speed: 0,
        eta: 0,
        stage_message: "Job queued for worker...",
        filename: extractedMedia?.title || "download",
      };

      setActiveJob(initialJob);
      showToast("Job Created", "Your media is now processing in the background.", "info");

      // Connect to SSE stream
      subscribeToJobEvents(job_id);
    } catch (err: any) {
      showToast("Job Error", err.message || "Failed to schedule job", "error");
    } finally {
      setIsLoading(false);
    }
  };

  // SSE Subscription
  const subscribeToJobEvents = (jobId: string) => {
    const eventSource = new EventSource(`${API_BASE_URL}/api/jobs/${jobId}/events`);

    eventSource.onmessage = (event) => {
      try {
        const update: JobProgressEvent = JSON.parse(event.data);
        setActiveJob(update);

        if (update.status === "COMPLETED") {
          showToast("Download Complete", "Your media is ready for download!", "success");
          eventSource.close();
        } else if (update.status === "FAILED" || update.status === "CANCELLED" || update.status === "EXPIRED") {
          eventSource.close();
        }
      } catch (err) {
        console.error("SSE parse error", err);
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
    };
  };

  const handleCancelJob = async () => {
    if (!activeJob) return;
    try {
      await cancelJob(activeJob.job_id);
      setActiveJob((prev) => (prev ? { ...prev, status: "CANCELLED", stage_message: "Job cancelled by user" } : null));
      showToast("Job Cancelled", "Download was stopped.", "info");
    } catch {
      // Ignored
    }
  };

  const handleReset = () => {
    setExtractedMedia(null);
    setActiveJob(null);
    setErrorInfo(null);
    setCurrentUrl("");
  };

  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground relative overflow-hidden">
      {/* Background Subtle Gradient Blobs */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-96 bg-gradient-to-b from-primary/15 via-blue-500/5 to-transparent blur-3xl pointer-events-none -z-10" />

      <Header />

      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 sm:py-16 space-y-16">
        {/* Hero Section */}
        <section className="text-center space-y-5 max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-semibold backdrop-blur-md">
            <Sparkles className="w-3.5 h-3.5" />
            <span>High-Speed Universal Media Engine</span>
          </div>

          <h1 className="text-4xl sm:text-6xl font-black tracking-tight text-foreground leading-[1.1]">
            Download Media. <span className="bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400 bg-clip-text text-transparent">Simply.</span>
          </h1>

          <p className="text-base sm:text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed">
            Download supported videos, audio, images and playlists with a fast, modern media downloader.
          </p>

          {/* Main URL Input Component */}
          <div className="pt-4">
            <UrlInput onAnalyze={handleAnalyze} isLoading={isLoading} initialUrl={currentUrl} />
          </div>

          {/* Quick Platform Supported Badges */}
          <div className="flex flex-wrap items-center justify-center gap-2 pt-2 text-xs text-muted-foreground">
            <span className="text-[11px] font-medium mr-1">Supported Platforms:</span>
            {["YouTube", "Instagram", "TikTok", "X / Twitter", "SoundCloud", "Vimeo", "Pinterest", "Reddit"].map((p) => (
              <span key={p} className="px-2 py-0.5 rounded-md bg-card/60 border border-border/60 text-[11px]">
                {p}
              </span>
            ))}
          </div>
        </section>

        {/* Dynamic Workflow Area */}
        <section className="max-w-4xl mx-auto w-full transition-all">
          {isLoading && !extractedMedia && !activeJob && <LoadingState />}

          {errorInfo && !isLoading && (
            <ErrorState
              title={errorInfo.title}
              message={errorInfo.message}
              code={errorInfo.code}
              onRetry={() => handleAnalyze(currentUrl)}
              onReset={handleReset}
            />
          )}

          {activeJob && (
            <DownloadProgress job={activeJob} onCancel={handleCancelJob} onReset={handleReset} />
          )}

          {extractedMedia && !activeJob && (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-300">
              <MediaPreview media={extractedMedia} />
              <FormatSelector media={extractedMedia} onSubmitJob={handleSubmitJob} isSubmitting={isLoading} />
            </div>
          )}
        </section>

        {/* Feature Cards Grid */}
        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 pt-8">
          <div className="p-6 rounded-2xl border border-border/80 bg-card/40 backdrop-blur-md space-y-3 hover:border-primary/50 transition-all group">
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400 group-hover:scale-105 transition-transform">
              <Film className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-sm text-foreground">4K & Adaptive Video</h3>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Streams video and audio tracks separately and merges them seamlessly for maximum fidelity.
            </p>
          </div>

          <div className="p-6 rounded-2xl border border-border/80 bg-card/40 backdrop-blur-md space-y-3 hover:border-emerald-500/50 transition-all group">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 group-hover:scale-105 transition-transform">
              <Music className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-sm text-foreground">320kbps Audio Mastering</h3>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Lossless conversion to MP3, M4A, Opus, and WAV formats with customizable bitrate profiles.
            </p>
          </div>

          <div className="p-6 rounded-2xl border border-border/80 bg-card/40 backdrop-blur-md space-y-3 hover:border-amber-500/50 transition-all group">
            <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 group-hover:scale-105 transition-transform">
              <ImageIcon className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-sm text-foreground">Gallery & ZIP Bundling</h3>
            <p className="text-xs text-muted-foreground leading-relaxed">
              First-class multi-image extraction with selective checkboxes and one-click ZIP packaging.
            </p>
          </div>

          <div className="p-6 rounded-2xl border border-border/80 bg-card/40 backdrop-blur-md space-y-3 hover:border-purple-500/50 transition-all group">
            <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 group-hover:scale-105 transition-transform">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-sm text-foreground">SSRF & Ephemeral Security</h3>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Complete private subnet protection, sanitized headers, zero storage leaks, and automatic 60m cleanup.
            </p>
          </div>
        </section>

        {/* How It Works 4-Step Diagram */}
        <section className="rounded-3xl border border-border/80 bg-card/30 backdrop-blur-md p-8 sm:p-12 space-y-8">
          <div className="text-center space-y-2 max-w-xl mx-auto">
            <h2 className="text-2xl font-bold tracking-tight text-foreground">How It Works</h2>
            <p className="text-xs sm:text-sm text-muted-foreground">
              A frictionless four-step media conversion pipeline designed for speed and reliability.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { step: "01", title: "Paste URL", desc: "Input any supported video, audio, image gallery, or playlist URL." },
              { step: "02", title: "Extract Streams", desc: "Engine verifies safety and extracts available media stream manifests." },
              { step: "03", title: "Choose Format", desc: "Pick your preferred resolution, audio bitrate, or select gallery images." },
              { step: "04", title: "Stream Download", desc: "Download directly to your device via standard HTTP headers with no path leaks." },
            ].map((s) => (
              <div key={s.step} className="p-5 rounded-2xl bg-background/50 border border-border/60 space-y-2 relative">
                <span className="text-2xl font-mono font-black text-primary/40 block">{s.step}</span>
                <h4 className="font-bold text-sm text-foreground">{s.title}</h4>
                <p className="text-xs text-muted-foreground leading-relaxed">{s.desc}</p>
              </div>
            ))}
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}

export default function HomePage() {
  return (
    <ToastProvider>
      <DownloaderApp />
    </ToastProvider>
  );
}
