"use client";

import * as React from "react";
import { Header } from "../../components/Header";
import { Footer } from "../../components/Footer";
import {
  ShieldAlert,
  Server,
  HardDrive,
  Cpu,
  RefreshCcw,
  Lock,
  CheckCircle2,
  AlertTriangle,
  LogOut,
  Layers,
} from "lucide-react";
import { formatBytes } from "../../lib/utils";
import { API_BASE_URL } from "../../lib/api";

interface AdminMetrics {
  status: string;
  ytdlp_version: string;
  ffmpeg_path: string;
  storage: {
    total_bytes: number;
    used_bytes: number;
    free_bytes: number;
    active_job_directories: number;
  };
  limits: {
    max_file_size_mb: number;
    max_playlist_items: number;
    download_expiry_seconds: number;
  };
}

export default function AdminDashboardPage() {
  const [adminToken, setAdminToken] = React.useState<string>("");
  const [isAuthenticated, setIsAuthenticated] = React.useState<boolean>(false);
  const [metrics, setMetrics] = React.useState<AdminMetrics | null>(null);
  const [isLoading, setIsLoading] = React.useState<boolean>(false);
  const [errorMsg, setErrorMsg] = React.useState<string | null>(null);

  // Check sessionStorage on load
  React.useEffect(() => {
    const saved = sessionStorage.getItem("admin_token");
    if (saved) {
      setAdminToken(saved);
      fetchMetrics(saved);
    }
  }, []);

  const fetchMetrics = async (tokenToUse: string) => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/admin/metrics`, {
        headers: { "x-admin-token": tokenToUse },
      });

      if (res.status === 401 || res.status === 403) {
        setIsAuthenticated(false);
        sessionStorage.removeItem("admin_token");
        throw new Error("Invalid admin authorization token.");
      }

      if (!res.ok) {
        throw new Error(`Failed to load metrics: HTTP ${res.status}`);
      }

      const data = await res.json();
      setMetrics(data);
      setIsAuthenticated(true);
      sessionStorage.setItem("admin_token", tokenToUse);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to authenticate.");
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (adminToken.trim()) {
      fetchMetrics(adminToken.trim());
    }
  };

  const handleLogout = () => {
    sessionStorage.removeItem("admin_token");
    setIsAuthenticated(false);
    setMetrics(null);
    setAdminToken("");
  };

  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground">
      <Header />

      <main className="flex-1 max-w-6xl mx-auto px-4 sm:px-6 py-10 w-full space-y-8">
        {/* Title Bar */}
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border/80 pb-6">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-400 text-xs font-semibold mb-2">
              <ShieldAlert className="w-3.5 h-3.5" />
              Administrative Telemetry
            </div>
            <h1 className="text-2xl sm:text-3xl font-black tracking-tight">Engine Admin Portal</h1>
          </div>

          {isAuthenticated && (
            <div className="flex items-center gap-3">
              <button
                onClick={() => fetchMetrics(adminToken)}
                disabled={isLoading}
                className="px-4 py-2 text-xs font-semibold rounded-xl border border-border bg-card hover:bg-muted text-foreground transition-all flex items-center gap-1.5"
              >
                <RefreshCcw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
                Refresh
              </button>
              <button
                onClick={handleLogout}
                className="px-4 py-2 text-xs font-semibold rounded-xl border border-rose-500/30 bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 transition-all flex items-center gap-1.5"
              >
                <LogOut className="w-3.5 h-3.5" />
                Sign Out
              </button>
            </div>
          )}
        </div>

        {/* Auth Gate */}
        {!isAuthenticated ? (
          <div className="max-w-md mx-auto p-8 rounded-2xl border border-border/80 bg-card/70 backdrop-blur-xl shadow-2xl space-y-6 text-center">
            <div className="w-12 h-12 rounded-2xl bg-primary/10 border border-primary/20 text-primary mx-auto flex items-center justify-center">
              <Lock className="w-6 h-6" />
            </div>

            <div className="space-y-1.5">
              <h3 className="text-lg font-bold">Admin Authorization Required</h3>
              <p className="text-xs text-muted-foreground">
                Enter your administrative security token (configured via <code className="text-primary font-mono">ADMIN_SECRET_KEY</code>)
              </p>
            </div>

            {errorMsg && (
              <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs">
                {errorMsg}
              </div>
            )}

            <form onSubmit={handleLogin} className="space-y-4">
              <input
                type="password"
                value={adminToken}
                onChange={(e) => setAdminToken(e.target.value)}
                placeholder="Enter admin token..."
                required
                className="w-full px-4 py-3 rounded-xl bg-background border border-border text-sm focus:outline-none focus:ring-2 focus:ring-primary font-mono text-center"
              />
              <button
                type="submit"
                disabled={isLoading || !adminToken.trim()}
                className="w-full py-3 rounded-xl bg-primary hover:bg-primary/90 text-white font-semibold text-sm shadow-lg shadow-primary/25 transition-all disabled:opacity-50"
              >
                {isLoading ? "Validating..." : "Authenticate"}
              </button>
            </form>
          </div>
        ) : (
          /* Live Dashboard View */
          metrics && (
            <div className="space-y-6">
              {/* Metrics Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="p-5 rounded-2xl border border-border/80 bg-card/60 backdrop-blur-md space-y-2">
                  <div className="flex items-center justify-between text-muted-foreground text-xs">
                    <span>Engine Status</span>
                    <Server className="w-4 h-4 text-emerald-400" />
                  </div>
                  <div className="text-xl font-black text-foreground flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
                    Online
                  </div>
                  <div className="text-[11px] text-muted-foreground">FastAPI + Redis Active</div>
                </div>

                <div className="p-5 rounded-2xl border border-border/80 bg-card/60 backdrop-blur-md space-y-2">
                  <div className="flex items-center justify-between text-muted-foreground text-xs">
                    <span>Extractor Core</span>
                    <Cpu className="w-4 h-4 text-blue-400" />
                  </div>
                  <div className="text-xl font-black font-mono text-primary truncate">
                    {metrics.ytdlp_version}
                  </div>
                  <div className="text-[11px] text-muted-foreground">Latest Stable Release</div>
                </div>

                <div className="p-5 rounded-2xl border border-border/80 bg-card/60 backdrop-blur-md space-y-2">
                  <div className="flex items-center justify-between text-muted-foreground text-xs">
                    <span>Storage Free</span>
                    <HardDrive className="w-4 h-4 text-amber-400" />
                  </div>
                  <div className="text-xl font-black font-mono text-foreground">
                    {formatBytes(metrics.storage.free_bytes)}
                  </div>
                  <div className="text-[11px] text-muted-foreground">
                    {formatBytes(metrics.storage.used_bytes)} used of {formatBytes(metrics.storage.total_bytes)}
                  </div>
                </div>

                <div className="p-5 rounded-2xl border border-border/80 bg-card/60 backdrop-blur-md space-y-2">
                  <div className="flex items-center justify-between text-muted-foreground text-xs">
                    <span>Active Workspaces</span>
                    <Layers className="w-4 h-4 text-purple-400" />
                  </div>
                  <div className="text-xl font-black font-mono text-purple-400">
                    {metrics.storage.active_job_directories}
                  </div>
                  <div className="text-[11px] text-muted-foreground">Auto-sweep every 60s</div>
                </div>
              </div>

              {/* Engine Configuration Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="p-6 rounded-2xl border border-border/80 bg-card/60 backdrop-blur-md space-y-4">
                  <h3 className="text-sm font-bold text-foreground">Operational Safety Bounds</h3>
                  <div className="space-y-3 text-xs">
                    <div className="flex items-center justify-between p-3 rounded-xl bg-background/50 border border-border/60">
                      <span className="text-muted-foreground">Max File Size Limit:</span>
                      <span className="font-mono font-semibold text-foreground">
                        {metrics.limits.max_file_size_mb} MB
                      </span>
                    </div>
                    <div className="flex items-center justify-between p-3 rounded-xl bg-background/50 border border-border/60">
                      <span className="text-muted-foreground">Max Playlist Items:</span>
                      <span className="font-mono font-semibold text-foreground">
                        {metrics.limits.max_playlist_items} items
                      </span>
                    </div>
                    <div className="flex items-center justify-between p-3 rounded-xl bg-background/50 border border-border/60">
                      <span className="text-muted-foreground">Ephemeral File Retention:</span>
                      <span className="font-mono font-semibold text-emerald-400">
                        {metrics.limits.download_expiry_seconds}s (60 min)
                      </span>
                    </div>
                  </div>
                </div>

                <div className="p-6 rounded-2xl border border-border/80 bg-card/60 backdrop-blur-md space-y-4">
                  <h3 className="text-sm font-bold text-foreground">Binaries & Subprocesses</h3>
                  <div className="space-y-3 text-xs">
                    <div className="flex items-center justify-between p-3 rounded-xl bg-background/50 border border-border/60">
                      <span className="text-muted-foreground">Media Processor:</span>
                      <span className="font-mono font-semibold text-foreground">
                        {metrics.ffmpeg_path}
                      </span>
                    </div>
                    <div className="flex items-center justify-between p-3 rounded-xl bg-background/50 border border-border/60">
                      <span className="text-muted-foreground">Subprocess Execution:</span>
                      <span className="font-mono font-semibold text-emerald-400">
                        Zero Shell (Argument Arrays)
                      </span>
                    </div>
                    <div className="flex items-center justify-between p-3 rounded-xl bg-background/50 border border-border/60">
                      <span className="text-muted-foreground">SSRF Pre-flight Engine:</span>
                      <span className="font-mono font-semibold text-emerald-400">
                        Active (IPv4 & IPv6 CIDR)
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )
        )}
      </main>

      <Footer />
    </div>
  );
}
