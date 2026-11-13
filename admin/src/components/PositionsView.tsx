"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "@/lib/client";

type TableKey = "full" | "legacy";

type Position = {
  id: number;
  region_dept: string | null;
  recruit_unit: string | null;
  position_name: string | null;
  position_code: string | null;
  position_nature: string | null;
  quota: number | null;
  education: string | null;
  major: string | null;
  year: number | null;
  city: string | null;
  province_code: string | null;
  is_disability_only: boolean;
  remote_area: boolean;
  is_active: boolean;
  audience_tags: string[] | null;
  source_id: number | null;
  source_name: string | null;
  announcement_id: number | null;
  source_url: string | null;
  announcement_title: string | null;
  announcement_exam_type: string | null;
  updated_at: string;
};

type ListRes = { items: Position[]; total: number; page: number; pageSize: number };

type GroupRes = {
  groups: {
    year: number | null;
    province_code: string | null;
    province_name: string | null;
    total: number;
    disability_only: number;
  }[];
  years: { year: number; total: number }[];
  provinces: { province_code: string | null; province_name: string | null; total: number }[];
};

type SourcesRes = {
  items: { id: number; source_name: string; province_code: string | null; full_count: number; legacy_count: number }[];
  unassigned: { full_count: number; legacy_count: number };
};

const PAGE_SIZE = 20;

const META: Record<TableKey, { title: string; desc: string; empty: string }> = {
  full: {
    title: "全量岗位库",
    desc: "主数据表 positions_full：所有采集数据都写这张表",
    empty: "全量库暂无数据。流水线导入端（import_data.py）会把新采集的数据写入这张表。",
  },
  legacy: {
    title: "残疾人专岗库",
    desc: "positions：手工整理的残疾人专岗 + 采集时自动识别同步的残疾专项岗位，新数据同时保留在全量库",
    empty: "暂无残疾人专岗数据。",
  },
};

export default function PositionsView({ table }: { table: TableKey }) {
  const meta = META[table];

  const [data, setData] = useState<ListRes | null>(null);
  const [groups, setGroups] = useState<GroupRes | null>(null);
  const [sources, setSources] = useState<SourcesRes | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const [groupMode, setGroupMode] = useState<"year" | "province">("year");
  const [q, setQ] = useState("");
  const [year, setYear] = useState("");
  const [province, setProvince] = useState("");
  const [source, setSource] = useState("");
  const [disability, setDisability] = useState(false);
  const [page, setPage] = useState(1);

  const [detail, setDetail] = useState<Record<string, unknown> | null>(null);

  const load = useCallback(
    async (p: number) => {
      setLoading(true);
      setError("");
      try {
        const params = new URLSearchParams({
          table,
          page: String(p),
          pageSize: String(PAGE_SIZE),
        });
        if (q) params.set("q", q);
        if (year) params.set("year", year);
        if (province) params.set("province", province);
        if (source) params.set("source", source);
        if (disability) params.set("disability", "1");
        setData(await api<ListRes>(`/api/positions?${params}`));
      } catch (e) {
        setError(e instanceof Error ? e.message : "加载失败");
      } finally {
        setLoading(false);
      }
    },
    [table, q, year, province, source, disability]
  );

  useEffect(() => {
    load(page);
  }, [load, page]);

  useEffect(() => {
    setData(null);
    setPage(1);
    setYear("");
    setProvince("");
    setSource("");
    setQ("");
    setDisability(false);
    api<GroupRes>(`/api/groups?table=${table}`).then(setGroups).catch(() => {});
    api<SourcesRes>("/api/sources").then(setSources).catch(() => {});
  }, [table]);

  async function toggleActive(row: Position) {
    await api(`/api/positions/${row.id}?table=${table}`, {
      method: "PATCH",
      body: JSON.stringify({ is_active: !row.is_active }),
    });
    load(page);
  }

  async function openDetail(id: number) {
    const res = await api<{ item: Record<string, unknown> }>(
      `/api/positions/${id}?table=${table}`
    );
    setDetail(res.item);
  }

  const yearCards = useMemo(
    () => (groups?.years ?? []).map((y) => ({ key: String(y.year), label: `${y.year} 年度`, total: y.total })),
    [groups]
  );
  const provinceCards = useMemo(
    () =>
      (groups?.provinces ?? []).map((p) => ({
        key: p.province_code ?? "",
        label: p.province_name ?? "未标注省份",
        total: p.total,
      })),
    [groups]
  );

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;
  const sourceOptions = (sources?.items ?? []).filter((s) =>
    table === "full" ? s.full_count > 0 : s.legacy_count > 0
  );

  return (
    <div>
      <h1 className="text-xl font-bold text-slate-800">{meta.title}</h1>
      <p className="mb-4 mt-1 text-sm text-slate-500">{meta.desc}</p>

      {/* 分组浏览：年度 / 省份 */}
      <div className="mb-4 rounded-xl bg-white p-4 shadow-sm">
        <div className="mb-3 flex items-center gap-2">
          <span className="text-sm font-medium text-slate-600">分组浏览</span>
          <div className="ml-1 flex rounded-lg bg-slate-100 p-0.5 text-xs">
            {(
              [
                ["year", "按考试年度"],
                ["province", "按省区"],
              ] as const
            ).map(([k, label]) => (
              <button
                key={k}
                onClick={() => setGroupMode(k)}
                className={`rounded-md px-3 py-1 ${
                  groupMode === k ? "bg-white font-medium text-slate-800 shadow-sm" : "text-slate-500"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          {(groupMode === "year" ? yearCards : provinceCards).map((card) => {
            const active =
              groupMode === "year" ? year === card.key : province === card.key;
            return (
              <button
                key={card.key}
                onClick={() => {
                  if (groupMode === "year") {
                    setYear(active ? "" : card.key);
                  } else {
                    setProvince(active ? "" : card.key);
                  }
                  setPage(1);
                }}
                className={`rounded-lg border px-3 py-2 text-left text-sm ${
                  active
                    ? "border-blue-500 bg-blue-50 text-blue-700"
                    : "border-slate-200 bg-white text-slate-700 hover:border-slate-300"
                }`}
              >
                <div className="font-medium">{card.label}</div>
                <div className="text-xs text-slate-400">{card.total} 个岗位</div>
              </button>
            );
          })}
          {groups && yearCards.length === 0 && provinceCards.length === 0 && (
            <span className="text-sm text-slate-400">暂无数据</span>
          )}
        </div>
      </div>

      {/* 筛选栏 */}
      <div className="mb-4 flex flex-wrap items-center gap-3 rounded-xl bg-white p-4 shadow-sm">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && (setPage(1), load(1))}
          placeholder="搜索岗位名 / 单位 / 代码"
          className="w-56 rounded-lg border border-slate-300 px-3 py-1.5 text-sm outline-none focus:border-blue-500"
        />
        <select
          value={year}
          onChange={(e) => {
            setYear(e.target.value);
            setPage(1);
          }}
          className="rounded-lg border border-slate-300 px-2 py-1.5 text-sm outline-none focus:border-blue-500"
        >
          <option value="">全部年度</option>
          {(groups?.years ?? []).map((y) => (
            <option key={y.year} value={y.year}>
              {y.year} 年度（{y.total}）
            </option>
          ))}
        </select>
        <select
          value={province}
          onChange={(e) => {
            setProvince(e.target.value);
            setPage(1);
          }}
          className="rounded-lg border border-slate-300 px-2 py-1.5 text-sm outline-none focus:border-blue-500"
        >
          <option value="">全部省区</option>
          {(groups?.provinces ?? []).map((p) => (
            <option key={p.province_code ?? "none"} value={p.province_code ?? ""}>
              {p.province_name}（{p.total}）
            </option>
          ))}
        </select>
        <select
          value={source}
          onChange={(e) => {
            setSource(e.target.value);
            setPage(1);
          }}
          className="rounded-lg border border-slate-300 px-2 py-1.5 text-sm outline-none focus:border-blue-500"
        >
          <option value="">全部来源</option>
          {sourceOptions.map((s) => (
            <option key={s.id} value={s.id}>
              {s.source_name}
            </option>
          ))}
          <option value="none">未标注来源</option>
        </select>
        <label className="flex items-center gap-2 text-sm text-slate-600">
          <input
            type="checkbox"
            checked={disability}
            onChange={(e) => {
              setDisability(e.target.checked);
              setPage(1);
            }}
          />
          仅看残疾专项
        </label>
        <button
          onClick={() => {
            setPage(1);
            load(1);
          }}
          className="rounded-lg bg-blue-600 px-4 py-1.5 text-sm text-white hover:bg-blue-700"
        >
          查询
        </button>
        <button
          onClick={() => {
            setQ("");
            setYear("");
            setProvince("");
            setSource("");
            setDisability(false);
            setPage(1);
          }}
          className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm text-slate-600"
        >
          重置
        </button>
        <span className="ml-auto text-sm text-slate-500">{data ? `共 ${data.total} 条` : ""}</span>
      </div>

      {error && <p className="mb-3 text-red-600">{error}</p>}

      <div className="overflow-x-auto rounded-xl bg-white shadow-sm">
        <table className="w-full min-w-[1120px] text-sm">
          <thead className="bg-slate-50 text-left text-slate-500">
            <tr>
              <th className="px-3 py-2.5">职位名称</th>
              <th className="px-3 py-2.5">招录单位</th>
              <th className="px-3 py-2.5">人数</th>
              <th className="px-3 py-2.5">学历</th>
              <th className="px-3 py-2.5">年度</th>
              <th className="px-3 py-2.5">省区 / 城市</th>
              <th className="px-3 py-2.5">数据来源</th>
              <th className="px-3 py-2.5">考试公告</th>
              <th className="px-3 py-2.5">标记</th>
              <th className="px-3 py-2.5">状态</th>
              <th className="px-3 py-2.5"></th>
            </tr>
          </thead>
          <tbody>
            {data?.items.map((r) => (
              <tr key={r.id} className="border-t border-slate-100 hover:bg-slate-50">
                <td className="max-w-52 truncate px-3 py-2.5">
                  <button
                    className="text-left font-medium text-blue-600 hover:underline"
                    onClick={() => openDetail(r.id)}
                  >
                    {r.position_name ?? "—"}
                  </button>
                </td>
                <td className="max-w-44 truncate px-3 py-2.5 text-slate-600">
                  {r.recruit_unit ?? "—"}
                </td>
                <td className="px-3 py-2.5 text-slate-600">{r.quota ?? "—"}</td>
                <td className="max-w-32 truncate px-3 py-2.5 text-slate-600">
                  {r.education ?? "—"}
                </td>
                <td className="px-3 py-2.5 text-slate-600">{r.year ?? "—"}</td>
                <td className="px-3 py-2.5 text-slate-600">
                  {r.province_code ?? "—"}
                  {r.city ? ` / ${r.city}` : ""}
                </td>
                <td className="max-w-40 truncate px-3 py-2.5 text-xs">
                  {r.source_name ? (
                    <span className="rounded bg-sky-50 px-1.5 py-0.5 text-sky-700">
                      {r.source_name}
                    </span>
                  ) : (
                    <span className="text-slate-300">—</span>
                  )}
                </td>
                <td className="px-3 py-2.5">
                  {r.source_url ? (
                    <a
                      href={r.source_url}
                      target="_blank"
                      rel="noreferrer"
                      title={r.announcement_title ?? r.source_url}
                      className="inline-flex items-center gap-1 rounded bg-blue-50 px-1.5 py-0.5 text-xs text-blue-700 hover:bg-blue-100"
                    >
                      查看公告 ↗
                    </a>
                  ) : (
                    <span className="text-xs text-slate-300">—</span>
                  )}
                </td>
                <td className="px-3 py-2.5">
                  <div className="flex gap-1">
                    {r.is_disability_only && (
                      <span className="rounded bg-amber-100 px-1.5 py-0.5 text-xs text-amber-700">
                        残疾专项
                      </span>
                    )}
                    {r.remote_area && (
                      <span className="rounded bg-emerald-100 px-1.5 py-0.5 text-xs text-emerald-700">
                        边远
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-3 py-2.5">
                  <button
                    onClick={() => toggleActive(r)}
                    className={`rounded-full px-2 py-0.5 text-xs ${
                      r.is_active
                        ? "bg-green-100 text-green-700"
                        : "bg-slate-200 text-slate-500"
                    }`}
                  >
                    {r.is_active ? "启用" : "停用"}
                  </button>
                </td>
                <td className="px-3 py-2.5 text-right">
                  <button
                    onClick={() => openDetail(r.id)}
                    className="text-xs text-slate-400 hover:text-blue-600"
                  >
                    详情
                  </button>
                </td>
              </tr>
            ))}
            {data && data.items.length === 0 && (
              <tr>
                <td colSpan={11} className="px-3 py-10 text-center text-slate-400">
                  {q || year || province || source || disability
                    ? "没有符合条件的岗位"
                    : meta.empty}
                </td>
              </tr>
            )}
            {!data && !error && (
              <tr>
                <td colSpan={11} className="px-3 py-10 text-center text-slate-400">
                  加载中…
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="mt-4 flex items-center justify-between text-sm text-slate-600">
        <button
          disabled={page <= 1 || loading}
          onClick={() => setPage(page - 1)}
          className="rounded-lg border border-slate-300 px-3 py-1.5 disabled:opacity-40"
        >
          上一页
        </button>
        <span>
          第 {page} / {totalPages} 页
        </span>
        <button
          disabled={page >= totalPages || loading}
          onClick={() => setPage(page + 1)}
          className="rounded-lg border border-slate-300 px-3 py-1.5 disabled:opacity-40"
        >
          下一页
        </button>
      </div>

      {detail && (
        <DetailModal
          detail={detail}
          table={table}
          onClose={() => {
            setDetail(null);
            load(page);
          }}
        />
      )}
    </div>
  );
}

function DetailModal({
  detail,
  table,
  onClose,
}: {
  detail: Record<string, unknown>;
  table: TableKey;
  onClose: () => void;
}) {
  const id = detail.id as number;
  const [flags, setFlags] = useState({
    is_active: Boolean(detail.is_active),
    is_disability_only: Boolean(detail.is_disability_only),
    remote_area: Boolean(detail.remote_area),
  });
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const skip = new Set([
    "raw_payload",
    "audience_tags",
    "is_active",
    "is_disability_only",
    "remote_area",
    "announcement_id",
    "source_url",
    "announcement_title",
  ]);

  async function save() {
    setSaving(true);
    try {
      await api(`/api/positions/${id}?table=${table}`, {
        method: "PATCH",
        body: JSON.stringify(flags),
      });
      setSaved(true);
      setTimeout(onClose, 600);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-8"
      onClick={onClose}
    >
      <div
        className="max-h-full w-full max-w-3xl overflow-auto rounded-xl bg-white p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-start justify-between">
          <h2 className="text-lg font-bold text-slate-800">
            {String(detail.position_name ?? "岗位详情")}（#{id}）
          </h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700">
            ✕
          </button>
        </div>

        {detail.source_url ? (
          <a
            href={String(detail.source_url)}
            target="_blank"
            rel="noreferrer"
            className="mb-4 flex items-center gap-3 rounded-lg border border-blue-100 bg-blue-50/60 p-3 hover:bg-blue-50"
          >
            <span className="text-lg">📢</span>
            <span className="min-w-0 flex-1">
              <span className="block text-sm font-medium text-blue-800">
                {String(detail.announcement_title ?? "查看考试公告")}
              </span>
              <span className="block truncate text-xs text-blue-500">
                {String(detail.source_url)}
              </span>
            </span>
            <span className="shrink-0 text-xs text-blue-600">一键直达 ↗</span>
          </a>
        ) : (
          <p className="mb-4 rounded-lg bg-slate-50 p-3 text-xs text-slate-400">
            该岗位没有记录公告出处（历史手工录入数据，无对应公告链接）
          </p>
        )}

        <div className="mb-4 flex flex-wrap gap-4 rounded-lg bg-slate-50 p-4 text-sm">
          {(
            [
              ["启用", "is_active"],
              ["残疾专项", "is_disability_only"],
              ["边远地区", "remote_area"],
            ] as const
          ).map(([label, key]) => (
            <label key={key} className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={flags[key]}
                onChange={(e) => {
                  setFlags({ ...flags, [key]: e.target.checked });
                  setSaved(false);
                }}
              />
              {label}
            </label>
          ))}
          <button
            onClick={save}
            disabled={saving}
            className="ml-auto rounded-lg bg-blue-600 px-4 py-1.5 text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? "保存中…" : saved ? "已保存 ✓" : "保存修改"}
          </button>
        </div>

        <dl className="grid grid-cols-[10rem_1fr] gap-x-4 text-sm">
          {Object.entries(detail)
            .filter(([k]) => !skip.has(k))
            .map(([k, v]) => (
              <div key={k} className="col-span-2 grid grid-cols-subgrid border-t border-slate-100 py-1.5">
                <dt className="text-slate-400">{k}</dt>
                <dd className="break-all text-slate-700">
                  {v === null || v === ""
                    ? "—"
                    : Array.isArray(v)
                      ? v.join("、")
                      : String(v)}
                </dd>
              </div>
            ))}
        </dl>
      </div>
    </div>
  );
}
