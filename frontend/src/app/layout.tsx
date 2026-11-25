import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";

import { SkipLink } from "@/components/layout/skip-link";
import { MotionPreference } from "@/components/layout/motion-preference";

import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "SAANS SAATHI AI — air intelligence for everyday breathing",
    template: "%s · SAANS SAATHI AI",
  },
  description:
    "A personal air-quality workspace for Indian cities: CPCB AQI context, household routines, indoor guidance, sustainability tracking and a grounded AI copilot.",
  applicationName: "SAANS SAATHI AI",
  keywords: [
    "air quality",
    "CPCB AQI",
    "PM2.5",
    "India",
    "air pollution",
    "environmental intelligence",
  ],
  robots: { index: true, follow: true },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#123d31",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className={inter.variable}>
        <MotionPreference />
        <SkipLink />
        {children}
      </body>
    </html>
  );
}
