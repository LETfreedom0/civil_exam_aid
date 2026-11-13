"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Shell from "@/components/Shell";
import { api } from "@/lib/client";

type Stats = {
  full: {
    total: number;
    active: number;
    disability_only: number;
    remote_area: number;
    linked: number;
    latest: string | null;
    groups: {
      year: number | null;
      province_code: string | null;
      province_name: string | null;
      total: number;
      disability_only: number;
    }[];
    years: { year: number; total: number }[];
  };
  legacy: {
    total: number;
    active: number;
    disability_only: number;
    linked: number;
    latest: string | null;
    byProvince: {
      province_code: string | null;
      province_name: string | null;
      total: number;
      disability_only: number;
    }[];
  };
  sources: {
    items: {
      id: number;
      source_name: string;
      province_code: string | null;
      count: number;
      full_count: number;
    }[];
    unassigned_legacy: number;
    unassigned_full: number;
  };
  announcements: {
    id: number;
    province_code: string | null;
    province_name: string | null;
    year: number | null;
    title: string | null;
    url: string | null;
    exam_type: string | null;
    count: number;
  }[];
  notices: { total: number; announcement: number; attachment: number };
};

function Card({
  label,
  value,
  sub,
  tone = "default",
}: {
  label: string;
  value: string | number;
  sub?: string;
  tone?: "default" | "muted";
}) {
  return (
    <div
      className={`rounded-xl p-5 shadow-sm ${
        tone === "muted" ? "bg-slate-50 ring-1 ring-slate-200" : "bg-white"
      }`}
    >
      <div className="text-sm text-slate-500">{label}</div>
      <div className="mt-1 text-2xl font-bold text-slate-800">{value}</div>
      {sub && <div className="mt-1 text-xs text-slate-400">{sub}</div>}
    </div>
  );
}

export default function DashboardPage() {
  const [data, setData] = useState<Stats | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<Stats>("/api/stats").then(setData).catch((e) => setError(e.message));
  }, []);

  return (
    <Shell>
      <h1 className="mb-4 text-xl font-bold text-slate-800">数据概览</h1>
      {error && <p className="text-red-600">加载失败：{error}</p>}
      {!data && !error && <p className="text-slate-500">加载中…</p>}

      {data && (
        <div className="space-y-6">
          {/* 全量库（主） */}
          <section>
            <div className="mb-2 flex items-center justify-between">
              <h2 className="font-semibold text-slate-700">全量岗位库（主数据）</h2>
              <Link href="/positions" className="text-sm text-blue-600 hover:underline">
                进入管理 →
              </Link>
            </div>
            {data.full.total === 0 ? (
              <div className="rounded-xl border border-dashed border-slate-300 bg-white p-6 text-sm text-slate-500">
                全量库 <code className="rounded bg-slate-100 px-1">positions_full</code> 目前为空。
                新采集的数据由导入端写入这张表后，这里会按考试年度与省区展示分布。
              </div>
            ) : (
              <>
                <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
                  <Card label="岗位总数" value={data.full.total} sub={`启用 ${data.full.active}`} />
                  <Card label="残疾专项岗位" value={data.full.disability_only} />
                  <Card label="边远地区岗位" value={data.full.remote_area} />
                  <Card
                    label="已关联考试公告"
                    value={data.full.linked}
                    sub={`覆盖率 ${data.full.total ? Math.round((data.full.linked / data.full.total) * 100) : 0}%`}
                  />
                  <Card
                    label="最近更新"
                    value={data.full.latest ? new Date(data.full.latest).toLocaleDateString("zh-CN") : "—"}
                  />
                </div>
                <div className="mt-4 rounded-xl bg-white p-5 shadow-sm">
                  <h3 className="mb-3 text-sm font-semibold text-slate-700">年度 × 省区分布</h3>
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-left text-slate-400">
                        <th className="pb-2">考试年度</th>
                        <th className="pb-2">省区</th>
                        <th className="pb-2">岗位数</th>
                        <th className="pb-2">残疾专项</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.full.groups.map((g, i) => (
                        <tr key={`${g.year}-${g.province_code}-${i}`} className="border-t border-slate-100">
                          <td className="py-2 text-slate-600">{g.year ?? "—"}</td>
                          <td className="py-2 text-slate-700">{g.province_name ?? "—"}</td>
                          <td className="py-2 font-medium text-slate-800">{g.total}</td>
                          <td className="py-2 text-amber-600">{g.disability_only}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </section>

          {/* 残疾人专岗库 */}
          <section className="rounded-xl bg-slate-50 p-5 ring-1 ring-slate-200">
            <div className="mb-3 flex items-center justify-between">
              <div>
                <h2 className="font-semibold text-slate-700">残疾人专岗库</h2>
                <p className="mt-0.5 text-xs text-slate-500">
                  手工整理的残疾人专岗 + 采集时自动识别的残疾专项岗位；新数据同时写入全量库
                </p>
              </div>
              <Link href="/legacy" className="text-sm text-blue-600 hover:underline">
                查看专岗库 →
              </Link>
            </div>
            <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
              <Card label="残疾人专岗" value={data.legacy.total} tone="muted" />
              <Card label="其中启用" value={data.legacy.active} tone="muted" />
              <Card label="覆盖省区" value={data.legacy.byProvince.length} tone="muted" />
              <Card
                label="最近更新"
                value={
                  data.legacy.latest ? new Date(data.legacy.latest).toLocaleDateString("zh-CN") : "—"
                }
                tone="muted"
              />
            </div>
          </section>

          {/* 考试公告 */}
          <section className="rounded-xl bg-white p-5 shadow-sm">
            <div className="mb-3 flex items-center justify-between">
              <div>
                <h2 className="font-semibold text-slate-700">考试公告</h2>
                <p className="mt-0.5 text-xs text-slate-500">
                  已登记 {data.announcements.length} 条公告页；岗位列表里点「查看公告」即可直达原官网
                </p>
              </div>
              <Link href="/notices" className="text-sm text-blue-600 hover:underline">
                全部公告 →
              </Link>
            </div>
            {data.announcements.length === 0 ? (
              <p className="text-sm text-slate-400">还没有登记考试公告</p>
            ) : (
              <ul className="divide-y divide-slate-100 text-sm">
                {data.announcements.map((a) => (
                  <li key={a.id} className="flex items-center gap-3 py-2.5">
                    <span className="w-24 shrink-0 text-slate-500">
                      {a.province_name ?? "—"} {a.year ?? ""}
                    </span>
                    <a
                      href={a.url ?? "#"}
                      target="_blank"
                      rel="noreferrer"
                      className="min-w-0 flex-1 truncate font-medium text-blue-600 hover:underline"
                    >
                      {a.title ?? a.url}
                    </a>
                    <span className="shrink-0 text-xs text-slate-400">
                      {a.exam_type ?? "—"} · 挂载 {a.count} 个岗位
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </section>

          {/* 数据来源 */}
          <section className="rounded-xl bg-white p-5 shadow-sm">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="font-semibold text-slate-700">数据来源</h2>
              <span className="text-xs text-slate-400">
                公告页 {data.notices.announcement} 条 · 采集附件 {data.notices.attachment} 个
              </span>
            </div>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-slate-400">
                  <th className="pb-2">来源名称</th>
                  <th className="pb-2">省区</th>
                  <th className="pb-2">全量库岗位数</th>
                  <th className="pb-2">专岗库岗位数</th>
                </tr>
              </thead>
              <tbody>
                {data.sources.items.map((s) => (
                  <tr key={s.id} className="border-t border-slate-100">
                    <td className="py-2 text-slate-700">{s.source_name}</td>
                    <td className="py-2 text-slate-600">{s.province_code ?? "—"}</td>
                    <td className="py-2 font-medium text-slate-800">{s.full_count}</td>
                    <td className="py-2 text-slate-600">{s.count}</td>
                  </tr>
                ))}
                {(data.sources.unassigned_full > 0 || data.sources.unassigned_legacy > 0) && (
                  <tr className="border-t border-slate-100">
                    <td className="py-2 text-slate-400">未标注来源</td>
                    <td className="py-2 text-slate-400">—</td>
                    <td className="py-2 text-slate-500">{data.sources.unassigned_full}</td>
                    <td className="py-2 text-slate-500">{data.sources.unassigned_legacy}</td>
                  </tr>
                )}
              </tbody>
            </table>
          </section>
        </div>
      )}
    </Shell>
  );
}
