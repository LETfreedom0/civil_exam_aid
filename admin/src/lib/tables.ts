export const TABLES = {
  full: {
    table: "positions_full",
    label: "全量岗位库",
    desc: "主数据表，后续所有采集与导入都写这里",
  },
  legacy: {
    table: "positions",
    label: "存量库（历史）",
    desc: "历史遗留数据，仅作参考，不再作为主数据维护",
  },
} as const;

export type TableKey = keyof typeof TABLES;

export function resolveTable(key?: string | null): TableKey {
  return key === "legacy" ? "legacy" : "full";
}

export function tableName(key?: string | null): string {
  return TABLES[resolveTable(key)].table;
}

/** 可编辑字段白名单（两张表同构） */
export const EDITABLE = new Set([
  "is_active",
  "is_disability_only",
  "remote_area",
  "audience_tags",
]);
