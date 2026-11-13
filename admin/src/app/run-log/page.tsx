"use client";

import { useCallback, useEffect, useState } from "react";
import Shell from "@/components/Shell";
import { api } from "@/lib/client";

type RunLog = {
  id: number;
  source_id: string;
  change_type: string;
  summary: string;
  affected_positions: number;
  created_at: string;
};

export default function RunLogPage() {
  const [data, setData] = useState<{ items: RunLog[]; total: number; page: number; pageSize: number } | null>(null);
  const [error, setError] = useState("");
  const [page, setPage] = useState(1);

  const load = useCallback(async () => {
    setError("");
    try {
      setData(await api(`/api/run_log?page=${page}&pageSize=30`));
    } catch (e) {
      setError(e instanceof Error ? e.message : "加载失败");
    }
  }, [page]);

  useEffect(() => {
    load();
  }, [load]);

  const totalPages = data ? Math.max(1, Math.ceil(data.total / 30)) : 1;

  return (
    <Shell>
      <h1 className="mb-4 text-xl font-bold text-slate-800">采集日志</h1>
      {error && <p className="mb-3 text-red-600">{error}</p>}

      <div className="rounded-xl bg-white shadow-sm">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-slate-500">
            <tr>
              <th className="px-4 py-2.5">时间</th>
              <th className="px-4 py-2.5">数据源</th>
              <th className="px-4 py-2.5">类型</th>
              <th className="px-4 py-2.5">摘要</th>
              <th className="px-4 py-2.5">影响岗位数</th>
            </tr>
          </thead>
          <tbody>
            {data?.items.map((r) => (
              <tr key={r.id} className="border-t border-slate-100">
                <td className="whitespace-nowrap px-4 py-2.5 text-slate-500">
                  {new Date(r.created_at).toLocaleString("zh-CN")}
                </td>
                <td className="px-4 py-2.5 text-slate-600">{r.source_id}</td>
                <td className="px-4 py-2.5">
                  <span className="rounded bg-blue-50 px-1.5 py-0.5 text-xs text-blue-700">
                    {r.change_type}
                  </span>
                </td>
                <td className="px-4 py-2.5 text-slate-700">{r.summary}</td>
                <td className="px-4 py-2.5 font-medium text-slate-800">{r.affected_positions}</td>
              </tr>
            ))}
            {data && data.items.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-slate-400">
                  暂无日志
                </td>
              </tr>
            )}
          </tbody>
        </table>
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
