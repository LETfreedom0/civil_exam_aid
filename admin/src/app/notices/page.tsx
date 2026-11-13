"use client";

import { useCallback, useEffect, useState } from "react";
import Shell from "@/components/Shell";
import { api } from "@/lib/client";

type Notice = {
  id: number;
  url: string;
  title: string | null;
  source_id: string | null;
  kind: "announcement" | "attachment";
  seen_at: string;
};

type Res = {
  items: Notice[];
  total: number;
  page: number;
  pageSize: number;
  stats: { announcement: number; attachment: number };
};

const TABS = [
  ["", "全部"],
  ["announcement", "考试公告"],
  ["attachment", "采集附件"],
] as const;

export default function NoticesPage() {
  const [data, setData] = useState<Res | null>(null);
  const [error, setError] = useState("");
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const [kind, setKind] = useState("");

  const load = useCallback(async () => {
    setError("");
    try {
      const params = new URLSearchParams({ page: String(page), pageSize: "20" });
      if (q) params.set("q", q);
      if (kind) params.set("kind", kind);
      setData(await api(`/api/notices?${params}`));
    } catch (e) {
      setError(e instanceof Error ? e.message : "加载失败");
    }
  }, [page, q, kind]);

  useEffect(() => {
    load();
  }, [load]);

  const totalPages = data ? Math.max(1, Math.ceil(data.total / 20)) : 1;

  return (
    <Shell>
      <h1 className="text-xl font-bold text-slate-800">考试公告</h1>
      <p className="mb-4 mt-1 text-sm text-slate-500">
        公告页是岗位「一键直达」的落点；采集附件是解析岗位数据用的原始表格
      </p>

      <div className="mb-4 flex flex-wrap items-center gap-3 rounded-xl bg-white p-4 shadow-sm">
        <div className="flex rounded-lg bg-slate-100 p-0.5 text-xs">
          {TABS.map(([k, label]) => (
            <button
              key={k}
              onClick={() => {
                setKind(k);
                setPage(1);
              }}
              className={`rounded-md px-3 py-1 ${
                kind === k ? "bg-white font-medium text-slate-800 shadow-sm" : "text-slate-500"
              }`}
            >
              {label}
              {k === "announcement" && data ? ` ${data.stats.announcement}` : ""}
              {k === "attachment" && data ? ` ${data.stats.attachment}` : ""}
            </button>
          ))}
        </div>
        <input
          value={q}
          onChange={(e) => {
            setQ(e.target.value);
            setPage(1);
          }}
          placeholder="搜索公告标题 / 地址"
          className="w-64 rounded-lg border border-slate-300 px-3 py-1.5 text-sm outline-none focus:border-blue-500"
        />
        <span className="ml-auto text-sm text-slate-500">{data ? `共 ${data.total} 条` : ""}</span>
      </div>

      {error && <p className="mb-3 text-red-600">{error}</p>}

      <div className="rounded-xl bg-white shadow-sm">
        <ul className="divide-y divide-slate-100">
          {data?.items.map((n) => {
            const isAnn = n.kind === "announcement";
            return (
              <li key={n.id} className="flex items-center gap-3 px-4 py-3 text-sm">
                <span className="text-base">{isAnn ? "📢" : "📎"}</span>
                <div className="min-w-0 flex-1">
                  <a
                    href={n.url}
                    target="_blank"
                    rel="noreferrer"
                    className="block truncate font-medium text-blue-600 hover:underline"
                  >
                    {n.title || n.url}
                  </a>
                  <div className="mt-0.5 truncate text-xs text-slate-400">
                    {n.source_id ? `采集源 ${n.source_id} · ` : ""}
                    发现于 {new Date(n.seen_at).toLocaleString("zh-CN")}
                  </div>
                </div>
                <span
                  className={`shrink-0 rounded px-1.5 py-0.5 text-xs ${
                    isAnn ? "bg-blue-50 text-blue-700" : "bg-slate-100 text-slate-500"
                  }`}
                >
                  {isAnn ? "公告页" : "附件"}
                </span>
                <a
                  href={n.url}
                  target="_blank"
                  rel="noreferrer"
                  className="shrink-0 text-xs text-slate-400 hover:text-blue-600"
                >
                  {isAnn ? "直达 ↗" : "下载 ↗"}
                </a>
              </li>
            );
          })}
          {data && data.items.length === 0 && (
            <li className="px-4 py-8 text-center text-slate-400">暂无公告</li>
          )}
        </ul>
      </div>

      <div className="mt-4 flex items-center justify-between text-sm text-slate-600">
        <button
          disabled={page <= 1}
          onClick={() => setPage(page - 1)}
          className="rounded-lg border border-slate-300 px-3 py-1.5 disabled:opacity-40"
        >
          上一页
        </button>
        <span>第 {page} / {totalPages} 页</span>
        <button
          disabled={page >= totalPages}
          onClick={() => setPage(page + 1)}
          className="rounded-lg border border-slate-300 px-3 py-1.5 disabled:opacity-40"
        >
          下一页
        </button>
      </div>
    </Shell>
  );
}
