import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "T&A Experience Stamp Map",
  description:
    "도시별 경험 지도, 여행 타임라인, 스탬프 스토리, 비식별 사업개발 리포트를 연결한 MyRealTrip T&A MVP"
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
