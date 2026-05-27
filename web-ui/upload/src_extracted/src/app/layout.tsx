import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Toaster as ShadcnToaster } from "@/components/ui/toaster";
import { Toaster as SonnerToaster } from "sonner";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "RhythmERP Automation Runner",
  description: "Automation test runner for Rhythm ERP modules. Run, monitor, and manage test suites for Common Settings, Commodity Settings, and more.",
  keywords: ["RhythmERP", "Automation", "Test Runner", "Selenium", "ERP"],
  authors: [{ name: "QA Team" }],
  icons: {
    icon: "https://z-cdn.chatglm.cn/z-ai/static/logo.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-background text-foreground`}
      >
        {children}
        <ShadcnToaster />
        <SonnerToaster
          position="bottom-right"
          theme="system"
          toastOptions={{
            style: { fontSize: '13px' },
          }}
          richColors
          closeButton
          duration={4000}
        />
      </body>
    </html>
  );
}
