import Link from "next/link";
import { DownloadCloud, ArrowLeft, HelpCircle } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-background text-foreground px-4">
      <div className="max-w-md w-full text-center space-y-6 p-8 rounded-2xl border border-border/80 bg-card/60 backdrop-blur-xl shadow-2xl">
        <div className="w-16 h-16 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary mx-auto">
          <DownloadCloud className="w-8 h-8" />
        </div>

        <div className="space-y-2">
          <span className="text-4xl font-mono font-black text-primary">404</span>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Page Not Found</h1>
          <p className="text-xs text-muted-foreground leading-relaxed">
            The page you are looking for might have been moved, removed, or is temporarily unavailable.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
          <Link
            href="/"
            className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-primary hover:bg-primary/90 text-primary-foreground text-xs font-semibold flex items-center justify-center gap-2 transition-all"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Home
          </Link>
          <Link
            href="/faq"
            className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-muted/60 hover:bg-muted text-muted-foreground hover:text-foreground text-xs font-semibold flex items-center justify-center gap-2 transition-all border border-border/60"
          >
            <HelpCircle className="w-4 h-4" />
            Help & FAQ
          </Link>
        </div>
      </div>
    </div>
  );
}
