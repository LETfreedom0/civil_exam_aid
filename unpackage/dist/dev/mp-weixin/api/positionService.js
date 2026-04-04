"use strict";
const common_vendor = require("../common/vendor.js");
const common_supabase = require("../common/supabase.js");
const provinces = [
  {
    code: "110000",
    name: "北京"
  },
  {
    code: "120000",
    name: "天津"
  },
  {
    code: "130000",
    name: "河北"
  },
  {
    code: "140000",
    name: "山西"
  },
  {
    code: "150000",
    name: "内蒙古"
  },
  {
    code: "210000",
    name: "辽宁"
  },
  {
    code: "220000",
    name: "吉林"
  },
  {
    code: "230000",
    name: "黑龙江"
  },
  {
    code: "310000",
    name: "上海"
  },
  {
    code: "320000",
    name: "江苏"
  },
  {
    code: "330000",
    name: "浙江"
  },
  {
    code: "340000",
    name: "安徽"
  },
  {
    code: "350000",
    name: "福建"
  },
  {
    code: "360000",
    name: "江西"
  },
  {
    code: "370000",
    name: "山东"
  },
  {
    code: "410000",
    name: "河南"
  },
  {
    code: "420000",
    name: "湖北"
  },
  {
    code: "430000",
    name: "湖南"
  },
  {
    code: "440000",
    name: "广东"
  },
  {
    code: "450000",
    name: "广西"
  },
  {
    code: "460000",
    name: "海南"
  },
  {
    code: "500000",
    name: "重庆"
  },
  {
    code: "510000",
    name: "四川"
  },
  {
    code: "520000",
    name: "贵州"
  },
  {
    code: "530000",
    name: "云南"
  },
  {
    code: "540000",
    name: "西藏"
  },
  {
    code: "610000",
    name: "陕西"
  },
  {
    code: "620000",
    name: "甘肃"
  },
  {
    code: "630000",
    name: "青海"
  },
  {
    code: "640000",
    name: "宁夏"
  },
  {
    code: "650000",
    name: "新疆"
  },
  {
    code: "660000",
    name: "兵团"
  }
];
const positionService = {
  // 获取职位列表
  async getPositions(params = {}) {
    let query = common_supabase.supabase.from("positions").select("*");
    if (params.provinceCode) {
      query = query.eq("province_code", params.provinceCode);
    } else if (params.city) {
      query = query.eq("city", params.city);
    }
    if (params.year) {
      query = query.eq("year", params.year);
    }
    const { data, error } = await query;
    if (error)
      throw error;
    let result = Array.isArray(data) ? data : [];
    if (params.keyword) {
      const k = String(params.keyword).toLowerCase();
      result = result.filter((p) => {
        const name = (p.position_name || "").toLowerCase();
        const unit = (p.recruit_unit || "").toLowerCase();
        const desc = (p.description || "").toLowerCase();
        const major = (p.major || "").toLowerCase();
        return name.includes(k) || unit.includes(k) || desc.includes(k) || major.includes(k);
      });
    }
    if (params.examType) {
      if (params.examType === "省考") {
        result = result.filter((p) => p.position_origin === 0);
      } else if (params.examType === "事业编") {
        result = result.filter((p) => p.position_origin === 1);
      }
    }
    return result;
  },
  // 获取所有可选城市
  async getCities() {
    return this.getProvinces();
  },
  // 获取所有可选省份/城市
  async getProvinces() {
    return provinces;
  },
  // 获取职位详情
  async getPositionById(id) {
    if (!id || id === "undefined" || id === "null") {
      throw new Error("Invalid position ID");
    }
    const { data, error } = await common_supabase.supabase.from("positions").select("*").eq("id", id).single();
    if (error)
      throw error;
    return data;
  },
  // 获取考试时间线
  async getExamTimeline(provinceCode, year) {
    try {
      const { data, error } = await common_supabase.supabase.from("exam_timelines").select("*").eq("province_code", provinceCode).eq("year", year).single();
      if (error || !data) {
        common_vendor.index.__f__("warn", "at api/positionService.js:82", "未找到时间线数据，使用模拟数据", error);
        return {
          signup_start: "2026-01-22",
          signup_end: "2026-01-26",
          payment_end: "2026-01-28",
          admit_card_start: "2026-02-20",
          exam_date: "2026-02-25",
          score_date: "2026-03-20",
          interview_date_start: "2026-04-15"
        };
      }
      return data;
    } catch (e) {
      common_vendor.index.__f__("error", "at api/positionService.js:96", "获取时间线失败", e);
      return null;
    }
  },
  // 获取数据更新统计信息
  async getUpdateStats() {
    const { data, error } = await common_supabase.supabase.from("positions").select("*");
    if (error)
      throw error;
    const list = Array.isArray(data) ? data : [];
    return {
      lastUpdateTime: "",
      newPositionsCount: 0,
      totalPositionsCount: list.length,
      updatedProvinces: []
    };
  },
  // 获取更新日志列表
  async getUpdateLogs() {
    return [];
  },
  // 提交报错反馈
  async submitReport(reportData) {
    common_vendor.index.__f__("log", "at api/positionService.js:124", "调用 submitReport 方法:", reportData);
    try {
      const data = {
        position_id: reportData.position_id,
        position_name: reportData.position_name,
        report_type: reportData.report_type,
        description: reportData.description,
        user_ip: reportData.user_ip || ""
      };
      common_vendor.index.__f__("log", "at api/positionService.js:134", "发送 POST 请求:", { data });
      return new Promise((resolve, reject) => {
        common_vendor.index.request({
          url: "https://hubbzosfrhxnzwuiitcv.supabase.co/rest/v1/report_feedback",
          method: "POST",
          header: {
            "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh1YmJ6b3Nmcmh4bnp3dWlpdGN2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjkzNDI4NTEsImV4cCI6MjA4NDkxODg1MX0.Xvo9xHl6jyNcbjoImq4phJnR0Na1zUGpQWLnGTNLsfo",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh1YmJ6b3Nmcmh4bnp3dWlpdGN2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjkzNDI4NTEsImV4cCI6MjA4NDkxODg1MX0.Xvo9xHl6jyNcbjoImq4phJnR0Na1zUGpQWLnGTNLsfo",
            "Content-Type": "application/json",
            "Accept": "application/json"
          },
          data,
          success: (res) => {
            var _a;
            common_vendor.index.__f__("log", "at api/positionService.js:149", "收到响应:", res);
            if (res.statusCode >= 200 && res.statusCode < 300) {
              resolve(res.data);
            } else {
              reject(new Error(`请求失败: ${res.statusCode} ${((_a = res.data) == null ? void 0 : _a.message) || "未知错误"}`));
            }
          },
          fail: (err) => {
            common_vendor.index.__f__("error", "at api/positionService.js:157", "请求失败:", err);
            reject(err);
          }
        });
      });
    } catch (e) {
      common_vendor.index.__f__("error", "at api/positionService.js:163", "提交反馈异常:", e);
      throw e;
    }
  }
};
exports.positionService = positionService;
//# sourceMappingURL=../../.sourcemap/mp-weixin/api/positionService.js.map
