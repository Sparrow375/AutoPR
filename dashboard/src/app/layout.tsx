import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AutoPR Dashboard",
  description:
    "Context-aware work item to pull request agent — real-time pipeline monitoring dashboard",
  keywords: ["AutoPR", "AI", "code generation", "pull request", "pipeline"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
