const { Pool } = require("pg");

// 连接池放在模块顶层：SCF 实例复用时避免每次调用重新建连（压冷启动延迟的关键）
const pool = new Pool({
  connectionString: process.env.DB_CONNECTION_STRING,
  ssl: { rejectUnauthorized: false },
  max: 3,
  idleTimeoutMillis: 30_000,
  connectionTimeoutMillis: 8_000,
});

function ok(data, extra = {}) {
  return { ok: true, data, ...extra };
}

function fail(message) {
  return { ok: false, error: String(message || "unknown error").slice(0, 300) };
}

function q(text, values = []) {
  return pool.query(text, values);
}

// ---------------------------------------------------------------- positions

async function getPositions(event) {
  const conds = [];
  const values = [];
  const add = (sql, val) => {
    values.push(val);
    conds.push(`${sql} $${values.length}`);
  };

  if (event.provinceCode) add("province_code =", String(event.provinceCode));
  if (event.city) add("city =", String(event.city));
  if (event.year) add("year =", Number(event.year));
  if (event.disabilityOnly === true) add("is_disability_only =", true);

  let sql = "SELECT * FROM positions";
  if (conds.length) sql += " WHERE " + conds.join(" AND ");
  sql += " ORDER BY year DESC, province_code, position_code LIMIT 3000";

  const { rows } = await q(sql, values);

  // keyword / examType 与原前端逻辑一致，放服务端做，减少传输量
  let result = rows;
  if (event.keyword) {
    const k = String(event.keyword).toLowerCase();
    result = result.filter((p) =>
      [p.position_name, p.recruit_unit, p.description, p.major]
        .some((v) => String(v || "").toLowerCase().includes(k))
    );
  }
  if (event.examType === "省考") result = result.filter((p) => p.position_origin === 0);
  if (event.examType === "事业编") result = result.filter((p) => p.position_origin === 1);

  return result;
}

async function getPositionById(event) {
  const id = Number(event.id);
  if (!Number.isInteger(id)) throw new Error("Invalid position ID");
  const { rows } = await q("SELECT * FROM positions WHERE id = $1 LIMIT 1", [id]);
  return rows[0] || null;
}

// ------------------------------------------------------------ exam timelines

async function getExamTimeline(event) {
  const { rows } = await q(
    `SELECT * FROM exam_timelines
      WHERE province_code = $1 AND year = $2 AND category = $3
      LIMIT 1`,
    [String(event.provinceCode || ""), Number(event.year) || 0, Number(event.category) || 0]
  );
  return rows[0] || null;
}

// -------------------------------------------------------------------- stats

async function getStats() {
  const { rows } = await q(
    `SELECT p.province_code, COALESCE(pr.name, p.province_code) AS province_name,
            p.year, count(*)::int AS total,
            count(*) FILTER (WHERE p.is_disability_only)::int AS disability_only,
            max(p.updated_at) AS last_update
       FROM positions p
       LEFT JOIN provinces pr ON pr.code = p.province_code
      GROUP BY p.province_code, pr.name, p.year
      ORDER BY p.year DESC, total DESC`
  );
  const total = rows.reduce((s, r) => s + r.total, 0);
  return {
    total,
    lastUpdate: rows.reduce(
      (m, r) => (r.last_update && (!m || r.last_update > m) ? r.last_update : m),
      null
    ),
    groups: rows,
  };
}

// ------------------------------------------------------------------ feedback

async function submitReport(event, context) {
  const wxContext = context && (context.wxContext || context.USER_OPENID ? context.wxContext : null);
  const openid = wxContext && wxContext.OPENID ? wxContext.OPENID : null;

  const payload = {
    position_id: String(event.position_id || ""),
    position_name: String(event.position_name || ""),
    report_type: String(event.report_type || "other"),
    description: String(event.description || ""),
    user_ip: event.user_ip ? String(event.user_ip) : null,
    user_openid: openid,
  };
  if (!payload.position_id || !payload.position_name || !payload.description) {
    throw new Error("缺少必填字段：position_id / position_name / description");
  }

  // admin_app 无 report_feedback_id_seq 的 USAGE 权限（序列属 postgres 且无法授权），
  // 改为显式取 max(id)+1 插入；反馈量极小，无并发竞争问题
  const { rows: idRows } = await q("SELECT COALESCE(MAX(id),0)+1 AS next_id FROM report_feedback");
  const nextId = Number(idRows[0].next_id);

  const { rows } = await q(
    `INSERT INTO report_feedback
        (id, position_id, position_name, report_type, description, user_ip, user_openid, status, created_at, updated_at)
     VALUES ($1, $2, $3, $4, $5, $6, $7, 'pending', now(), now())
     RETURNING id, created_at`,
    [
      nextId,
      payload.position_id,
      payload.position_name,
      payload.report_type,
      payload.description,
      payload.user_ip,
      payload.user_openid,
    ]
  );
  return { id: rows[0] && rows[0].id };
}

// ---------------------------------------------------------------------- main

exports.main = async (event = {}, context = {}) => {
  // 只回传业务数据，绝不回传 event/context/process.env（可能含平台凭据）
  try {
    switch (event.action) {
      case "getPositions":
        return ok(await getPositions(event));
      case "getPositionById":
        return ok(await getPositionById(event));
      case "getExamTimeline":
        return ok(await getExamTimeline(event));
      case "getStats":
        return ok(await getStats());
      case "submitReport":
        return ok(await submitReport(event, context));
      default:
        return fail(`unknown action: ${String(event.action || "(empty)")}`);
    }
  } catch (e) {
    console.error("gwy-api error:", event.action, e && e.message);
    return fail(e && e.message ? e.message : e);
  }
};
