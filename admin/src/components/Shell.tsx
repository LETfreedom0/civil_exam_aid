"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { clearToken } from "@/lib/client";

const NAV = [
  { href: "/", label: "数据概览", icon: "📊" },
  { href: "/positions", label: "全量岗位库", icon: "🗂️" },
  { href: "/legacy", label: "残疾人专岗库", icon: "♿" },
  { href: "/notices", label: "招聘公告", icon: "📢" },
  { href: "/run-log", label: "采集日志", icon: "🕓" },
];

export default function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="flex min-h-screen bg-slate-100">
      <aside className="flex w-52 flex-col bg-slate-900 text-slate-100">
        <div className="px-5 py-5">
          <div className="text-base font-bold">公考岗位后台</div>
          <div className="mt-1 text-xs text-slate-400">残疾人公考数据管理</div>
        </div>
        <nav className="flex-1 space-y-1 px-3">
          {NAV.map((item) => {
            const active =
              item.href === "/"
                ? pathname === "/"
                : pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm ${
                  active
                    ? "bg-blue-600 text-white"
                    : "text-slate-300 hover:bg-slate-800"
                }`}
              >
                <span>{item.icon}</span>
                {item.label}
              </Link>
            );
          })}
        </nav>
        <button
          onClick={() => {
            clearToken();
            window.location.href = "/login";
          }}
          className="m-3 rounded-lg px-3 py-2 text-left text-sm text-slate-400 hover:bg-slate-800 hover:text-white"
        >
          退出登录
        </button>
      </aside>
      <main className="flex-1 overflow-auto p-6">{children}</main>
    </div>
  );
}
