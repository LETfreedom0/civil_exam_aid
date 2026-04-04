"use strict";
const common_vendor = require("../../common/vendor.js");
const api_positionService = require("../../api/positionService.js");
const _sfc_main = {
  data() {
    return {
      positions: [],
      provinceStats: [],
      totalPositions: 0,
      totalQuota: 0,
      currentYear: (/* @__PURE__ */ new Date()).getFullYear(),
      statusBarHeight: 0,
      customNavBarHeight: 0
    };
  },
  onLoad() {
    this.initSafeArea();
    this.loadData();
  },
  methods: {
    initSafeArea() {
      try {
        const app = getApp();
        if (app && app.globalData) {
          this.statusBarHeight = app.globalData.statusBarHeight || 20;
          this.customNavBarHeight = app.globalData.customNavBarHeight || 64;
        }
      } catch (e) {
        common_vendor.index.__f__("warn", "at pages/preview/preview.vue:83", "获取安全区域数据失败", e);
        this.statusBarHeight = 20;
        this.customNavBarHeight = 64;
      }
    },
    /**
     * 加载并统计数据
     */
    async loadData() {
      try {
        common_vendor.index.showLoading({ title: "加载中..." });
        const [provinceList, data] = await Promise.all([
          api_positionService.positionService.getProvinces(),
          api_positionService.positionService.getPositions({ year: this.currentYear })
        ]);
        this.positions = data;
        this.totalPositions = data.length;
        this.totalQuota = data.reduce((sum, p) => sum + (Number(p.quota) || 0), 0);
        const normalizeProvinceName = (name) => {
          if (!name)
            return "";
          const s = String(name).trim();
          return s.replace(/特别行政区$/g, "").replace(/维吾尔自治区$/g, "").replace(/壮族自治区$/g, "").replace(/回族自治区$/g, "").replace(/自治区$/g, "").replace(/省$/g, "").replace(/市$/g, "");
        };
        const statsMap = /* @__PURE__ */ new Map();
        const normalizedNameToCode = /* @__PURE__ */ new Map();
        provinceList.forEach((p) => {
          const code = p.code;
          statsMap.set(code, {
            province: p.name,
            code,
            count: 0
          });
          normalizedNameToCode.set(normalizeProvinceName(p.name), code);
        });
        data.forEach((p) => {
          const code = p.province_code || p.provinceCode;
          if (code && statsMap.has(code)) {
            statsMap.get(code).count++;
            return;
          }
          const provName = normalizeProvinceName(p.province || p.city);
          const mappedCode = normalizedNameToCode.get(provName);
          if (mappedCode && statsMap.has(mappedCode)) {
            statsMap.get(mappedCode).count++;
          }
        });
        this.provinceStats = Array.from(statsMap.values()).sort((a, b) => {
          if (b.count !== a.count) {
            return b.count - a.count;
          }
          return Number(a.code) - Number(b.code);
        });
      } catch (e) {
        common_vendor.index.__f__("error", "at pages/preview/preview.vue:156", e);
        common_vendor.index.showToast({ title: "数据加载失败", icon: "none" });
      } finally {
        common_vendor.index.hideLoading();
      }
    },
    /**
     * 跳转到指定省份的列表
     * @param {Object} item 省份对象
     */
    goToProvince(item) {
      common_vendor.index.navigateTo({
        url: `/pages/index/index?province=${item.province}&provinceCode=${item.code}`
      });
    },
    /**
     * 查看全部
     */
    viewAll() {
      common_vendor.index.navigateTo({
        url: "/pages/index/index"
      });
    }
  }
};
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return {
    a: $data.statusBarHeight + "px",
    b: common_vendor.t($data.currentYear),
    c: common_vendor.t($data.totalPositions),
    d: common_vendor.t($data.totalQuota),
    e: common_vendor.o((...args) => $options.viewAll && $options.viewAll(...args)),
    f: common_vendor.f($data.provinceStats, (item, index, i0) => {
      return common_vendor.e({
        a: common_vendor.t(item.province),
        b: item.count > 0
      }, item.count > 0 ? {
        c: common_vendor.t(item.count)
      } : {}, {
        d: item.count > 0 ? 1 : "",
        e: item.code || index,
        f: common_vendor.o(($event) => $options.goToProvince(item), item.code || index)
      });
    })
  };
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-2dad6c07"]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/preview/preview.js.map
