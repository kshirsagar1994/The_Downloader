"use client";

import * as React from "react";
import { logAdEvent } from "../../lib/adDiagnostics";

interface AdsterraBannerProps {
  idKey: string;
  width: number;
  height: number;
  label?: string;
  className?: string;
  responsiveScale?: boolean;
}

export function AdsterraBanner({
  idKey,
  width,
  height,
  label = "Advertisement",
  className = "",
  responsiveScale = true,
}: AdsterraBannerProps) {
  const containerRef = React.useRef<HTMLDivElement>(null);
  const [mounted, setMounted] = React.useState(false);
  const uniqueId = React.useId();

  // Log component mount
  React.useEffect(() => {
    setMounted(true);
    logAdEvent(`Banner_${idKey}_${width}x${height}`, "COMPONENT_MOUNTED", { width, height });
  }, [idKey, width, height]);

  // Generate iframe srcdoc content (renders immediately, not in useEffect)
  const getIframeSrcDoc = () => `
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>
          *, *::before, *::after { box-sizing: border-box; }
          html, body {
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
            background-color: transparent;
            display: flex;
            align-items: center;
            justify-content: center;
          }
        </style>
      </head>
      <body>
        <script type="text/javascript">
          atOptions = {
            'key' : '${idKey}',
            'format' : 'iframe',
            'height' : ${height},
            'width' : ${width},
            'params' : {}
          };
        <\/script>
        <script type="text/javascript" src="https://bellnewyork.org/22/${idKey}"><\/script>
      </body>
    </html>
  `;

  // This runs on mount to log events, but iframe is rendered directly
  React.useEffect(() => {
    if (!mounted || !containerRef.current) return;

    const container = containerRef.current;
    // Iframe is already rendered via srcdoc, just log
    logAdEvent(`Banner_${idKey}_${width}x${height}`, "IFRAME_RENDERED", { width, height });

    // Listen for iframe load/error if we can access it
    const iframe = container.querySelector("iframe");
    if (iframe) {
      iframe.onload = () => {
        logAdEvent(`Banner_${idKey}_${width}x${height}`, "IFRAME_LOADED", { width, height });
      };
      iframe.onerror = (e) => {
        logAdEvent(`Banner_${idKey}_${width}x${height}`, "IFRAME_ERROR", { error: String(e) });
      };
    }
  }, [mounted, idKey, width, height]);

  const iframeSrcDoc = getIframeSrcDoc();

  return (
    <div
      aria-label="Advertisement Banner"
      className={`flex flex-col items-center justify-center my-4 ${className}`}
    >
      {label && (
        <span className="text-[10px] uppercase tracking-wider text-muted-foreground/60 mb-1.5 select-none font-medium">
          {label}
        </span>
      )}
      <div
        className={`relative flex items-center justify-center overflow-hidden rounded-xl border border-border/40 bg-card/20 shadow-sm backdrop-blur-sm ${
          responsiveScale && width > 400 ? "max-w-full overflow-hidden" : ""
        }`}
        style={{
          width: responsiveScale && width > 400 ? undefined : `${width}px`,
          height: `${height}px`,
        }}
      >
        <div
          ref={containerRef}
          style={{ width: `${width}px`, height: `${height}px` }}
          className="flex items-center justify-center shrink-0"
        >
          <iframe
            width={width}
            height={height}
            style={{ border: "none", overflow: "hidden" }}
            scrolling="no"
            title={`${label} ${width}x${height}`}
            id={`ad-frame-${uniqueId.replace(/[^a-zA-Z0-9_-]/g, "")}`}
            srcDoc={iframeSrcDoc}
            sandbox="allow-scripts allow-same-origin allow-popups allow-forms allow-modals allow-top-navigation-by-user-activation"
          />
        </div>
      </div>
    </div>
  );
}
