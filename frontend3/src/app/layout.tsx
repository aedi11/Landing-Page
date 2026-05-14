// build: 2026-05-14
import type { Metadata, Viewport } from "next";
import { Inter, Space_Grotesk } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
  // Only load weights we actually use
  weight: ["400", "500", "600", "700"],
  preload: true,
});

const spaceGrotesk = Space_Grotesk({
  variable: "--font-space-grotesk",
  subsets: ["latin"],
  display: "swap",
  weight: ["500", "600", "700"],
  preload: true,
});

export const metadata: Metadata = {
  title: "AEDI — Automated Electronic Design Initiative",
  description:
    "Empowering India's hardware ecosystem through high-powered computing and AI-enabled Electronic Design Automation toolkits.",
  keywords: [
    "AEDI",
    "Electronic Design Automation",
    "EDA",
    "AI India",
    "Deep Tech",
    "NVIDIA Inception",
    "Hardware Innovation",
  ],
  // iOS Safari home-screen web app support
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
  },
};

// Separate viewport export (required by Next.js 14+)
export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  // Prevents iOS virtual keyboard from resizing the viewport and breaking fixed elements
  interactiveWidget: "resizes-content",
  themeColor: "#1E1B1B",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        {/* Preconnect to Next.js image optimization origin */}
        <link rel="preconnect" href="/_next" />
        {/* Preload the hero background image — it's above the fold */}
        <link
          rel="preload"
          as="image"
          href="/images/Background.png"
          fetchPriority="high"
        />
        {/* Preload the two logos visible in the hero without scrolling */}
        <link
          rel="preload"
          as="image"
          href="/images/iitd_logo.png"
        />
        <link
          rel="preload"
          as="image"
          href="/images/nvidia.png"
        />
      </head>
      <body
        className={`${inter.variable} ${spaceGrotesk.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
