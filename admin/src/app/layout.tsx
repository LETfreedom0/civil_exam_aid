import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "公考岗位后台管理",
  description: "残疾人公考岗位数据管理",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="zh-CN" className="h-full antialiased">
      <body className="min-h-full">{children}</body>
    </html>
  );
}
