import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Каталог",
  description: "Микросервис каталога",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru">
      <head>
      </head>
      <body>{children}</body>
    </html>
  );
}