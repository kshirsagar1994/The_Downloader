"use client";

import * as React from "react";

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

  React.useEffect(() => {
    setMounted(true);
  }, []);

  React.useEffect(() => {
    if (!mounted || !containerRef.current) return;

    const container = containerRef.current;
    // Clear any previous iframe
    container.innerHTML = "";

    const iframe = document.createElement("iframe");
    iframe.width = `${width}`;
    iframe.height = `${height}`;
    iframe.style.border = "none";
    iframe.style.overflow = "hidden";
    iframe.setAttribute("scrolling", "no");
    iframe.setAttribute("title", label || "Advertisement");

    container.appendChild(iframe);

    try {
      const doc = iframe.contentWindow?.document || iframe.contentDocument;
      if (doc) {
        doc.open();
        doc.write(`
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
        `);
        doc.close();
      }
    } catch (e) {
      console.warn("Failed to initialize Adsterra banner iframe", e);
    }

    return () => {
      if (container) {
        container.innerHTML = "";
      }
    };
  }, [mounted, idKey, width, height, label]);

  return (
    <div className={`flex flex-col items-center justify-center my-4 ${className}`}>
      {label && (
        <span className="text-[10px] uppercase tracking-wider text-muted-foreground/60 mb-1.5 select-none font-medium">
          {label}
        </span>
      )}
      <div
        className={`relative flex items-center justify-center overflow-hidden rounded-xl border border-border/40 bg-card/20 shadow-sm backdrop-blur-sm ${
          responsiveScale && width > 400 ? "max-w-full" : ""
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
        />
      </div>
    </div>
  );
}
