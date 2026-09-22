import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "HAIR CAPSTONE · AI Virtual Hairstyle",
  description: "A development preview of the HAIR CAPSTONE hairstyle transformation flow.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
