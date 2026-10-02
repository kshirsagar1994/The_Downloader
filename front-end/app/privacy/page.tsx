import type { Metadata } from "next";
import { Header } from "../../components/Header";
import { Footer } from "../../components/Footer";
import { ShieldCheck, Lock, Trash2, EyeOff } from "lucide-react";

export const metadata: Metadata = {
  title: "Privacy Policy — Universal Media Downloader",
  description: "Our strict zero-trace privacy policy, automated file removal, and ephemeral processing standards.",
};

export default function PrivacyPage() {
  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground">
      <Header />

      <main className="flex-1 max-w-4xl mx-auto px-4 sm:px-6 py-12 space-y-10">
        <div className="text-center space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold">
            <ShieldCheck className="w-3.5 h-3.5" />
            Zero-Trace Privacy
          </div>
          <h1 className="text-3xl sm:text-4xl font-black tracking-tight">Privacy Policy</h1>
          <p className="text-sm text-muted-foreground max-w-xl mx-auto">
            Your privacy and file security are strictly guaranteed by ephemeral isolation.
          </p>
        </div>

        <div className="prose prose-invert max-w-none space-y-6 text-sm text-muted-foreground leading-relaxed">
          <div className="p-6 rounded-2xl border border-border/80 bg-card/60 space-y-3">
            <h3 className="text-base font-bold text-foreground flex items-center gap-2">
              <Trash2 className="w-4 h-4 text-emerald-400" />
              1. Automated Ephemeral File Cleanup
            </h3>
            <p>
              When a user submits a media download request, files are temporarily stored inside an isolated UUID directory on the processing server. All downloaded videos, audios, image files, and temporary fragments are automatically and irreversibly deleted within 60 minutes after generation.
            </p>
          </div>

          <div className="p-6 rounded-2xl border border-border/80 bg-card/60 space-y-3">
            <h3 className="text-base font-bold text-foreground flex items-center gap-2">
              <EyeOff className="w-4 h-4 text-blue-400" />
              2. No User Identity or Activity Tracking
            </h3>
            <p>
              We do not track user identities, browsing histories, or download activities. No tracking cookies or advertising identifiers are used. The platform operates anonymously without mandatory account registration.
            </p>
          </div>

          <div className="p-6 rounded-2xl border border-border/80 bg-card/60 space-y-3">
            <h3 className="text-base font-bold text-foreground flex items-center gap-2">
              <Lock className="w-4 h-4 text-purple-400" />
              3. Data Security & Protocol Encryption
            </h3>
            <p>
              All interactions between your browser and our extraction servers are encrypted via HTTPS (TLS 1.3). Media delivery utilizes secure, temporary streaming tokens that prevent unauthorized access.
            </p>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
