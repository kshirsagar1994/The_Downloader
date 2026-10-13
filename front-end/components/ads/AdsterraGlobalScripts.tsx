"use client";

import * as React from "react";
import Script from "next/script";
import { logAdEvent } from "../../lib/adDiagnostics";

const POPUNDER_SRC = "https://accountut.com/1/e4a8db086145e255eb3dd3e35c07d1e4";
const SOCIAL_BAR_SRC = "https://bellnewyork.org/14/719dbaa2b0800fd9cb1801ece80b6cd9";

export function AdsterraGlobalScripts() {
  React.useEffect(() => {
    logAdEvent("Global_Popunder", "SCRIPT_REQUESTED", { src: POPUNDER_SRC });
    logAdEvent("Global_SocialBar", "SCRIPT_REQUESTED", { src: SOCIAL_BAR_SRC });
  }, []);

  return (
    <>
      {/* Adsterra Popunder */}
      <Script
        id="adsterra-popunder"
        src={POPUNDER_SRC}
        strategy="afterInteractive"
        data-cfasync="false"
        onLoad={() => {
          logAdEvent("Global_Popunder", "SCRIPT_LOADED", { src: POPUNDER_SRC });
        }}
        onError={(e) => {
          logAdEvent("Global_Popunder", "SCRIPT_ERROR", { src: POPUNDER_SRC, error: String(e) });
        }}
      />

      {/* Adsterra Social Bar */}
      <Script
        id="adsterra-socialbar"
        src={SOCIAL_BAR_SRC}
        strategy="afterInteractive"
        data-cfasync="false"
        onLoad={() => {
          logAdEvent("Global_SocialBar", "SCRIPT_LOADED", { src: SOCIAL_BAR_SRC });
        }}
        onError={(e) => {
          logAdEvent("Global_SocialBar", "SCRIPT_ERROR", { src: SOCIAL_BAR_SRC, error: String(e) });
        }}
      />
    </>
  );
}
