import type { Metadata } from "next";
import { JetBrains_Mono, Poppins, Roboto } from "next/font/google";
import { ThemeProvider } from "next-themes";
import "./globals.css";
import { Toaster } from "sonner";
import { QueryProvider } from "@/components/providers/QueryProvider";
import { ErrorBoundary } from "@/components/ErrorBoundary";

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const poppins = Poppins({
  variable: "--font-poppins",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
});

const roboto = Roboto({
  variable: "--font-roboto",
  subsets: ["latin"],
  weight: ["400", "500", "700"],
});

export const metadata: Metadata = {
  title: "agDi - RhythmERP Automation Runner",
  description: "Agricultural Digital Intelligence - Internal QA tool for running Selenium/pytest tests against RhythmERP system",
  icons: {
    icon: "/agdi-logo.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet" />
      </head>
      <body
        className={`${jetbrainsMono.variable} ${poppins.variable} ${roboto.variable} antialiased bg-background text-foreground`}
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="light"
          enableSystem
          disableTransitionOnChange
        >
          <QueryProvider><ErrorBoundary>{children}</ErrorBoundary></QueryProvider>
          <Toaster
            position="bottom-right"
            richColors
            closeButton
            duration={3500}
            toastOptions={{
              classNames: {
                toast: "font-['Poppins'] text-[13px] rounded-xl shadow-lg border",
                title: "font-semibold",
                description: "text-[12px] opacity-80",
                closeButton: "rounded-full",
              },
            }}
          />
        </ThemeProvider>
      </body>
    </html>
  );
}
