import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Admin Monitoring Portal — Universal Media Downloader",
  description: "Real-time engine metrics, storage utilization, and system health.",
};

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <div className="min-h-screen bg-background">{children}</div>;
}
