import type { Metadata } from "next";
import { Header } from "../../components/Header";
import { Footer } from "../../components/Footer";
import { HelpCircle, Shield, FileVideo, Music, Layers } from "lucide-react";

export const metadata: Metadata = {
  title: "FAQ & Supported Formats — Universal Media Downloader",
  description: "Frequently asked questions about media extraction, video formats, audio transcode, and platform compatibility.",
};

const FAQS = [
  {
    q: "How does the Universal Media Downloader work?",
    a: "When you paste a link, our backend analyzes the streaming manifest using our high-speed extraction engine. It identifies available video tracks, audio channels, and image galleries. When you request a download, our background worker downloads the optimal streams, merges them losslessly if required, and serves the clean media file to your browser.",
  },
  {
    q: "Why do some 1080p and 4K videos require merging?",
    a: "Modern streaming platforms store high-definition video (1080p, 1440p, 4K) and audio in separate adaptive DASH/HLS streams. Our engine downloads both streams simultaneously and merges them losslessly into a single high-definition MP4 container.",
  },
  {
    q: "How does the Image Downloader and ZIP archiving work?",
    a: "If a URL contains photos, gallery cards, or multiple high-resolution assets, you can select individual items or click 'Select All'. Our worker packages your selection into a standard clean ZIP archive for instant one-click download.",
  },
  {
    q: "How are temporary files and my privacy handled?",
    a: "We do not store your downloads permanently. Every job is executed in an isolated temporary directory that is automatically deleted within 60 minutes or immediately upon error. We do not retain download history, IP logs, or personal identity records.",
  },
  {
    q: "What security and SSRF safeguards are implemented?",
    a: "Our backend enforces pre-flight DNS hostname resolution and strictly blocks connections to internal IP addresses, loopbacks, private RFC1918 subnets, and cloud metadata services. Argument arrays prevent command injection, and filename sanitizers eliminate path traversal risks.",
  },
];

export default function FaqPage() {
  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground">
      <Header />

      <main className="flex-1 max-w-4xl mx-auto px-4 sm:px-6 py-12 space-y-12">
        <div className="text-center space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-semibold">
            <HelpCircle className="w-3.5 h-3.5" />
            Knowledge Base
          </div>
          <h1 className="text-3xl sm:text-4xl font-black tracking-tight">Frequently Asked Questions</h1>
          <p className="text-sm text-muted-foreground max-w-xl mx-auto">
            Everything you need to know about formats, conversion pipelines, and engine mechanics.
          </p>
        </div>

        <div className="space-y-4">
          {FAQS.map((faq, idx) => (
            <div
              key={idx}
              className="p-6 rounded-2xl border border-border/80 bg-card/60 backdrop-blur-md space-y-2 shadow-sm"
            >
              <h3 className="font-bold text-base text-foreground flex items-start gap-2.5">
                <span className="text-primary font-mono text-sm font-black">Q{idx + 1}.</span>
                {faq.q}
              </h3>
              <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed pl-7">
                {faq.a}
              </p>
            </div>
          ))}
        </div>
      </main>

      <Footer />
    </div>
  );
}
