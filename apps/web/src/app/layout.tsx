import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";
import "./workspace.css";
const dmSans = localFont({
  src: "./fonts/dm-sans-variable.ttf",
  variable: "--font-dm-sans",
  weight: "100 1000",
  display: "swap",
});
export const metadata: Metadata = {
  title: "Form — Engineering Academy",
  description:
    "A personal academy for backend and applied AI engineering. Build understanding through deliberate practice.",
};
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={dmSans.variable}>
      <body>
        <a href="#main-content" className="skip-link">
          Skip to content
        </a>
        {children}
      </body>
    </html>
  );
}
