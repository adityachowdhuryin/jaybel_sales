import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Sales and analytics agent",
  description: "Jaybel sales analytics — natural language to SQL",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
