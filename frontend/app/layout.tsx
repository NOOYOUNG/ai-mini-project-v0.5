import "./globals.css";
import type { ReactNode } from "react";

export const metadata = { title: "기술 전략 분석 에이전트" };

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
