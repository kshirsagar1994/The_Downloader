/**
 * Adsterra Advertising Diagnostic & Observability Utility
 * 
 * Provides structured tracking for ad lifecycle events:
 * 1. COMPONENT_MOUNTED: React component successfully rendered into DOM
 * 2. SCRIPT_REQUESTED: Network script element created & appended
 * 3. SCRIPT_LOADED: Script load event fired (HTTP response received)
 * 4. CONTAINER_INITIALIZED: DOM container element prepared for ad injection
 * 5. IFRAME_LOADED: Ad iframe document created and loaded
 * 
 * NOTE: Third-party script HTTP 200 does NOT guarantee an ad was filled or an
 * impression was monetized. Actual delivery & revenue MUST be verified via the
 * Adsterra Publisher Dashboard.
 */

export type AdEventType =
  | "COMPONENT_MOUNTED"
  | "SCRIPT_REQUESTED"
  | "SCRIPT_LOADED"
  | "SCRIPT_ERROR"
  | "CONTAINER_INITIALIZED"
  | "IFRAME_LOADED"
  | "IFRAME_ERROR"
  | "WARNING";

export interface AdDiagnosticEvent {
  timestamp: string;
  unit: string;
  type: AdEventType;
  details?: Record<string, unknown>;
}

declare global {
  interface Window {
    __AD_DIAGNOSTICS_LOG__?: AdDiagnosticEvent[];
    __DEBUG_ADS__?: boolean;
  }
}

export function logAdEvent(unit: string, type: AdEventType, details?: Record<string, unknown>): void {
  if (typeof window === "undefined") return;

  const event: AdDiagnosticEvent = {
    timestamp: new Date().toISOString(),
    unit,
    type,
    details,
  };

  // Maintain in-memory diagnostic log for inspection in DevTools
  if (!window.__AD_DIAGNOSTICS_LOG__) {
    window.__AD_DIAGNOSTICS_LOG__ = [];
  }
  window.__AD_DIAGNOSTICS_LOG__.push(event);

  // Check if debug mode is active (URL param ?debug_ads=true, window flag, or dev environment)
  const isDebug =
    Boolean(window.__DEBUG_ADS__) ||
    (typeof window !== "undefined" &&
      new URLSearchParams(window.location.search).get("debug_ads") === "true") ||
    process.env.NODE_ENV !== "production";

  if (isDebug) {
    const style =
      type.includes("ERROR")
        ? "color: #ef4444; font-weight: bold;"
        : type === "SCRIPT_LOADED" || type === "IFRAME_LOADED"
        ? "color: #10b981; font-weight: bold;"
        : "color: #3b82f6;";

    console.log(`%c[Adsterra Diagnostics] [${type}] ${unit}`, style, details || "");
  }
}
