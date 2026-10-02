import type { Metadata } from "next";
import { Header } from "../../components/Header";
import { Footer } from "../../components/Footer";
import { FileCode, Shield, Layers, Server } from "lucide-react";

export const metadata: Metadata = {
  title: "Third-Party Software Notices — The_Downloader",
  description: "Open-source software licenses, third-party notices, and attribution information for The_Downloader.",
};

const NOTICES = [
  {
    name: "Redis",
    repo: "https://github.com/redis/redis",
    license: "BSD 3-Clause (Redis 7.2.x)",
    desc: "Redis 7.2.x and earlier remain licensed under the BSD 3-Clause license. Pinned in production deployment.",
  },
  {
    name: "FastAPI & Uvicorn",
    repo: "https://github.com/fastapi/fastapi",
    license: "MIT / BSD 3-Clause",
    desc: "High-performance Python ASGI backend and web server.",
  },
  {
    name: "Next.js & React",
    repo: "https://github.com/vercel/next.js",
    license: "MIT",
    desc: "Frontend user interface framework and runtime components.",
  },
  {
    name: "Tailwind CSS & Lucide Icons",
    repo: "https://github.com/tailwindlabs/tailwindcss",
    license: "MIT / ISC",
    desc: "Modern styling engine and open-source interface icons.",
  },
];

export default function NoticesPage() {
  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground">
      <Header />

      <main className="flex-1 max-w-4xl mx-auto px-4 sm:px-6 py-12 space-y-10">
        <div className="text-center space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-semibold">
            <FileCode className="w-3.5 h-3.5" />
            Open Source & Compliance
          </div>
          <h1 className="text-3xl sm:text-4xl font-black tracking-tight">Third-Party Notices</h1>
          <p className="text-sm text-muted-foreground max-w-xl mx-auto">
            The_Downloader is built with and utilizes third-party open-source software. All third-party licenses remain applicable to their respective components.
          </p>
        </div>

        <div className="space-y-4">
          {NOTICES.map((n, idx) => (
            <div
              key={idx}
              className="p-6 rounded-2xl border border-border/80 bg-card/60 backdrop-blur-md space-y-2 shadow-sm"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h3 className="font-bold text-base text-foreground flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-primary" />
                  {n.name}
                </h3>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-medium bg-muted/60 text-muted-foreground border border-border/60">
                  {n.license}
                </span>
              </div>
              <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
                {n.desc}
              </p>
              <div className="pt-1">
                <a
                  href={n.repo}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-primary hover:underline font-mono"
                >
                  {n.repo}
                </a>
              </div>
            </div>
          ))}
        </div>

        <div className="p-6 rounded-2xl border border-border/80 bg-card/40 space-y-2 text-xs text-muted-foreground">
          <h4 className="font-semibold text-foreground text-sm flex items-center gap-1.5">
            <Shield className="w-4 h-4 text-emerald-400" />
            Proprietary Code Separation & Disclaimer
          </h4>
          <p>
            The_Downloader&apos;s original source code is proprietary software owned by Kshirsagar (Copyright &copy; 2026). Third-party open-source licenses apply strictly to the respective third-party components. Use of third-party software does not imply affiliation or endorsement.
          </p>
        </div>
      </main>

      <Footer />
    </div>
  );
}
