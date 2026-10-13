"use client";

import * as React from "react";

interface AdsterraNativeBannerProps {
  className?: string;
  title?: string;
}

export function AdsterraNativeBanner({
  className = "",
  title = "Sponsored Recommendations",
}: AdsterraNativeBannerProps) {
  const containerRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // Check if script has already been attached to document
    const existingScript = document.querySelector(
      'script[src="https://bellnewyork.org/21/793c0b65bb7a09a035194e02bf98a7f4"]'
    );

    if (!existingScript) {
      const script = document.createElement("script");
      script.async = true;
      script.setAttribute("data-cfasync", "false");
      script.src = "https://bellnewyork.org/21/793c0b65bb7a09a035194e02bf98a7f4";
      document.body.appendChild(script);
    }
  }, []);

  return (
    <section className={`w-full max-w-5xl mx-auto my-8 space-y-3 ${className}`}>
      <div className="flex items-center justify-between border-b border-border/50 pb-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-primary/70 animate-pulse" />
          {title}
        </span>
        <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20">
          Ad
        </span>
      </div>

      <div
        ref={containerRef}
        id="container-793c0b65bb7a09a035194e02bf98a7f4"
        className="w-full min-h-[160px] rounded-2xl border border-border/60 bg-card/30 backdrop-blur-md p-4 transition-all overflow-hidden"
      />
    </section>
  );
}
