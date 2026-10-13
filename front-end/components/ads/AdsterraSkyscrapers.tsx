"use client";

import * as React from "react";
import { AdsterraBanner } from "./AdsterraBanner";
import { X } from "lucide-react";
import { logAdEvent } from "../../lib/adDiagnostics";

const SKYSCRAPER_KEY = "658ad484883b0dacc600771800e4617c";

interface AdsterraSkyscrapersProps {
  rightKey?: string;
  leftKey?: string; // Optional: Only render if a distinct second placement key is provided
}

export function AdsterraSkyscrapers({
  rightKey = SKYSCRAPER_KEY,
  leftKey,
}: AdsterraSkyscrapersProps) {
  const [showRight, setShowRight] = React.useState(true);
  const [showLeft, setShowLeft] = React.useState(Boolean(leftKey));

  React.useEffect(() => {
    logAdEvent("Skyscraper_Container", "COMPONENT_MOUNTED", {
      rightKey,
      leftKey: leftKey || "not_configured",
    });
  }, [rightKey, leftKey]);

  return (
    <>
      {/* Optional Left Skyscraper (Rendered ONLY if a distinct left key is configured) */}
      {leftKey && showLeft && (
        <aside
          aria-label="Sponsored Advertisement Left"
          className="hidden min-[1680px]:flex flex-col items-center fixed left-3 top-28 z-30 transition-opacity"
        >
          <div className="relative group">
            <button
              type="button"
              onClick={() => {
                setShowLeft(false);
                logAdEvent("Skyscraper_Left", "WARNING", { action: "user_dismissed" });
              }}
              className="absolute -top-3 -right-2 p-1 rounded-full bg-background border border-border/70 text-muted-foreground hover:text-foreground shadow-sm transition-opacity opacity-70 group-hover:opacity-100"
              title="Close Ad"
            >
              <X className="w-3 h-3" />
            </button>
            <AdsterraBanner
              idKey={leftKey}
              width={160}
              height={600}
              label="Sponsored"
              responsiveScale={false}
            />
          </div>
        </aside>
      )}

      {/* Primary Right Skyscraper 160x600 (Desktop Gutter: >= 1680px) */}
      {showRight && (
        <aside
          aria-label="Sponsored Advertisement Right"
          className="hidden min-[1680px]:flex flex-col items-center fixed right-3 top-28 z-30 transition-opacity"
        >
          <div className="relative group">
            <button
              type="button"
              onClick={() => {
                setShowRight(false);
                logAdEvent("Skyscraper_Right", "WARNING", { action: "user_dismissed" });
              }}
              className="absolute -top-3 -right-2 p-1 rounded-full bg-background border border-border/70 text-muted-foreground hover:text-foreground shadow-sm transition-opacity opacity-70 group-hover:opacity-100"
              title="Close Ad"
            >
              <X className="w-3 h-3" />
            </button>
            <AdsterraBanner
              idKey={rightKey}
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
