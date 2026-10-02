import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Universal Media Downloader — Fast, High-Quality Video, Audio & Image Downloader",
  description: "Download videos, audios, playlists, and image galleries easily with real-time progress and high-speed precision.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-background text-foreground antialiased selection:bg-primary selection:text-white">
        {children}
      </body>
    </html>
  );
}
