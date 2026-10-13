import type { Metadata } from "next";
import Script from "next/script";
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

        {/* Adsterra Popunder */}
        <Script
          id="adsterra-popunder"
          src="https://accountut.com/1/e4a8db086145e255eb3dd3e35c07d1e4"
          strategy="afterInteractive"
          data-cfasync="false"
        />

        {/* Adsterra Social Bar */}
        <Script
          id="adsterra-socialbar"
          src="https://bellnewyork.org/14/719dbaa2b0800fd9cb1801ece80b6cd9"
          strategy="afterInteractive"
          data-cfasync="false"
        />
      </body>
    </html>
  );
}
