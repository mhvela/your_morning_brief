import React from "react";

export const metadata = {
  title: "Your Morning Brief",
  description: "Stay updated with your curated topics",
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
