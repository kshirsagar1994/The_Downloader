import type { Metadata } from "next";
import { Header } from "../../components/Header";
import { Footer } from "../../components/Footer";
import { Scale, AlertCircle, FileText } from "lucide-react";

export const metadata: Metadata = {
  title: "Terms of Service — Universal Media Downloader",
  description: "Terms of service and fair use guidelines for the Universal Media Downloader.",
};

export default function TermsPage() {
  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground">
      <Header />

      <main className="flex-1 max-w-4xl mx-auto px-4 sm:px-6 py-12 space-y-10">
        <div className="text-center space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-semibold">
            <Scale className="w-3.5 h-3.5" />
            Terms of Use
          </div>
          <h1 className="text-3xl sm:text-4xl font-black tracking-tight">Terms of Service</h1>
          <p className="text-sm text-muted-foreground max-w-xl mx-auto">
            Please read these terms carefully before utilizing our media extraction service.
          </p>
        </div>

        <div className="space-y-6 text-sm text-muted-foreground leading-relaxed">
          <div className="p-6 rounded-2xl border border-border/80 bg-card/60 space-y-3">
            <h3 className="text-base font-bold text-foreground flex items-center gap-2">
              <FileText className="w-4 h-4 text-primary" />
              1. Authorized Personal Use Only
            </h3>
            <p>
              The Universal Media Downloader is designed solely to facilitate the download of content that you own, hold authorization to access, or that is distributed under open public licenses (e.g. Creative Commons). You agree not to use this service to infringe upon copyrights, trademarks, or proprietary rights of content creators.
            </p>
          </div>

          <div className="p-6 rounded-2xl border border-border/80 bg-card/60 space-y-3">
            <h3 className="text-base font-bold text-foreground flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-amber-400" />
              2. Fair Usage & Rate Limitations
            </h3>
            <p>
              To protect server health and bandwidth availability for all users, rate limits and concurrent download caps are enforced. Any automated scraping, abusive hammering, or attempt to circumvent security protections is strictly prohibited.
            </p>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
