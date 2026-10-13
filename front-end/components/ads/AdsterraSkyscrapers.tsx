"use client";

import * as React from "react";
import { AdsterraBanner } from "./AdsterraBanner";
import { X } from "lucide-react";

export function AdsterraSkyscrapers() {
  const [showLeft, setShowLeft] = React.useState(true);
  const [showRight, setShowRight] = React.useState(true);

  return (
    <>
      {/* Left Skyscraper 160x600 (Desktop Gutter: >= 1680px) */}
      {showLeft && (
        <aside
          aria-label="Sponsored Advertisement Left"
          className="hidden min-[1680px]:flex flex-col items-center fixed left-3 top-24 z-30 transition-opacity"
        >
          <div className="relative group">
            <button
              type="button"
              onClick={() => setShowLeft(false)}
              className="absolute -top-3 -right-2 p-1 rounded-full bg-background border border-border/70 text-muted-foreground hover:text-foreground shadow-sm transition-opacity opacity-70 group-hover:opacity-100"
              title="Close Ad"
            >
              <X className="w-3 h-3" />
            </button>
            <AdsterraBanner
              idKey="658ad484883b0dacc600771800e4617c"
              width={160}
              height={600}
              label="Sponsored"
              responsiveScale={false}
            />
          </div>
        </aside>
      )}

      {/* Right Skyscraper 160x600 (Desktop Gutter: >= 1680px) */}
      {showRight && (
        <aside
          aria-label="Sponsored Advertisement Right"
          className="hidden min-[1680px]:flex flex-col items-center fixed right-3 top-24 z-30 transition-opacity"
        >
          <div className="relative group">
            <button
              type="button"
              onClick={() => setShowRight(false)}
              className="absolute -top-3 -right-2 p-1 rounded-full bg-background border border-border/70 text-muted-foreground hover:text-foreground shadow-sm transition-opacity opacity-70 group-hover:opacity-100"
              title="Close Ad"
            >
              <X className="w-3 h-3" />
            </button>
            <AdsterraBanner
              idKey="658ad484883b0dacc600771800e4617c"
              width={160}
              height={600}
              label="Sponsored"
              responsiveScale={false}
            />
          </div>
        </aside>
      )}
    </>
  );
}
