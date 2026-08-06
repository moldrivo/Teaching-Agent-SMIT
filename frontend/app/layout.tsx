import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Smit — Teaching Agent",
  description: "Your analytical AI coding instructor: Socratic guidance, code reviews, and bug hunts.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
