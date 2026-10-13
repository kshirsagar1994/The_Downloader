"use client";

import * as React from "react";
import { logAdEvent } from "../../lib/adDiagnostics";

const NATIVE_CONTAINER_ID = "container-793c0b65bb7a09a035194e02bf98a7f4";
const NATIVE_SCRIPT_SRC = "https://bellnewyork.org/21/793c0b65bb7a09a035194e02bf98a7f4";

interface AdsterraNativeBannerProps {
  className?: string;
  title?: string;
}

export function AdsterraNativeBanner({
  className = "",
  title = "Sponsored Recommendations",
}: AdsterraNativeBannerProps) {
  const containerRef = React.useRef<HTMLDivElement>(null);
  const scriptRef = React.useRef<HTMLScriptElement | null>(null);

  React.useEffect(() => {
    logAdEvent("NativeBanner_793c", "COMPONENT_MOUNTED", { containerId: NATIVE_CONTAINER_ID });

    const container = containerRef.current;
    if (!container) return;

    // Check for existing duplicate container in document
    const existingContainers = document.querySelectorAll(`[id="${NATIVE_CONTAINER_ID}"]`);
    if (existingContainers.length > 1) {
      console.warn(`[Adsterra Warning] Duplicate container ID detected: ${NATIVE_CONTAINER_ID}`);
    }

    logAdEvent("NativeBanner_793c", "CONTAINER_INITIALIZED", { containerId: NATIVE_CONTAINER_ID });

    // Clean any prior script instance attached by this component
    if (scriptRef.current && scriptRef.current.parentNode) {
      scriptRef.current.parentNode.removeChild(scriptRef.current);
    }

    // Create and attach new script instance for this container lifecycle
    const script = document.createElement("script");
    script.async = true;
    script.setAttribute("data-cfasync", "false");
    script.src = NATIVE_SCRIPT_SRC;

    script.onload = () => {
      logAdEvent("NativeBanner_793c", "SCRIPT_LOADED", { src: NATIVE_SCRIPT_SRC });
    };

    script.onerror = (e) => {
      logAdEvent("NativeBanner_793c", "SCRIPT_ERROR", { src: NATIVE_SCRIPT_SRC, error: String(e) });
    };

    scriptRef.current = script;
    logAdEvent("NativeBanner_793c", "SCRIPT_REQUESTED", { src: NATIVE_SCRIPT_SRC });
    container.appendChild(script);

    return () => {
      if (scriptRef.current && scriptRef.current.parentNode) {
        scriptRef.current.parentNode.removeChild(scriptRef.current);
        scriptRef.current = null;
      }
    };
  }, []);

  return (
    <section
      aria-label="Sponsored Content"
      className={`w-full max-w-5xl mx-auto my-8 space-y-3 ${className}`}
    >
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
        id={NATIVE_CONTAINER_ID}
        className="w-full min-h-[160px] rounded-2xl border border-border/60 bg-card/30 backdrop-blur-md p-4 transition-all overflow-hidden"
      />
    </section>
  );
}
