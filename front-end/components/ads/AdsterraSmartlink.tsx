"use client";

import * as React from "react";
import { ExternalLink, Tag } from "lucide-react";
import { logAdEvent } from "../../lib/adDiagnostics";

export const ADSTERRA_SMARTLINK_URL = "https://ardance.org/4/945a8cce411b1587d855795338599345";

interface SmartlinkProps {
  className?: string;
}

export function AdsterraSmartlinkBanner({ className = "" }: SmartlinkProps) {
  React.useEffect(() => {
    logAdEvent("Smartlink_Banner", "COMPONENT_MOUNTED", { url: ADSTERRA_SMARTLINK_URL });
  }, []);

  const handleClick = () => {
    logAdEvent("Smartlink_Banner", "SCRIPT_REQUESTED", { action: "user_click", destination: ADSTERRA_SMARTLINK_URL });
  };

  return (
    <div
      className={`relative overflow-hidden rounded-2xl border border-primary/25 bg-gradient-to-r from-primary/10 via-indigo-500/10 to-purple-500/10 p-4 sm:p-5 backdrop-blur-md transition-all hover:border-primary/45 shadow-sm group ${className}`}
    >
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3 text-left">
          <div className="w-10 h-10 rounded-xl bg-primary/20 border border-primary/30 flex items-center justify-center text-primary shrink-0 group-hover:scale-105 transition-transform">
            <Tag className="w-5 h-5 text-primary" />
          </div>
          <div className="space-y-0.5">
            <div className="flex items-center gap-2">
              <h4 className="font-bold text-sm text-foreground">
                Featured Partner Promotions
              </h4>
              <span className="text-[9px] font-bold px-1.5 py-0.5 rounded-full bg-primary/20 text-primary border border-primary/30 tracking-wider uppercase">
                Sponsored Ad
              </span>
            </div>
            <p className="text-xs text-muted-foreground leading-relaxed max-w-xl">
              Explore deals, software tools, and special promotions presented by our advertising partners.
            </p>
          </div>
        </div>

        <a
          href={ADSTERRA_SMARTLINK_URL}
          target="_blank"
          rel="noopener noreferrer nofollow sponsored"
          onClick={handleClick}
          className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-gradient-to-r from-primary via-blue-600 to-indigo-600 hover:from-primary/90 hover:to-indigo-500 text-white text-xs font-bold tracking-wide shadow-lg shadow-primary/20 hover:shadow-primary/30 transition-all shrink-0 flex items-center justify-center gap-1.5 group-hover:translate-x-0.5"
        >
          <span>Explore Partner Deals</span>
          <ExternalLink className="w-3.5 h-3.5 ml-0.5" />
        </a>
      </div>
    </div>
  );
}

export function AdsterraSmartlinkButton({ className = "" }: SmartlinkProps) {
  React.useEffect(() => {
    logAdEvent("Smartlink_Button", "COMPONENT_MOUNTED", { url: ADSTERRA_SMARTLINK_URL });
  }, []);

  const handleClick = () => {
    logAdEvent("Smartlink_Button", "SCRIPT_REQUESTED", { action: "user_click", destination: ADSTERRA_SMARTLINK_URL });
  };

  return (
    <a
      href={ADSTERRA_SMARTLINK_URL}
      target="_blank"
      rel="noopener noreferrer nofollow sponsored"
      onClick={handleClick}
      className={`px-3 py-1.5 rounded-xl border border-primary/40 bg-primary/10 hover:bg-primary/20 text-primary transition-all flex items-center gap-1.5 text-xs font-semibold shadow-sm hover:scale-[1.02] ${className}`}
      title="Sponsored Partner Offers (Advertisement)"
    >
      <Tag className="w-3.5 h-3.5 text-primary" />
      <span>Sponsored Deals</span>
      <ExternalLink className="w-3 h-3 opacity-70" />
    </a>
  );
}
