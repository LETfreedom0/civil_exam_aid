"use strict";
const common_vendor = require("../../common/vendor.js");
const api_positionService = require("../../api/positionService.js");
const PositionCard = () => "../../components/PositionCard.js";
const _sfc_main = {
  components: {
    PositionCard
  },
  data() {
    return {
      searchKeyword: "",
      currentYear: 2026,
      currentProvince: "",
      currentProvinceCode: "",
      currentExamType: "",
      provinces: [],
      allPositions: [],
      positions: [],
      examTypeCounts: {
        all: 0,
        provincial: 0,
        enterprise: 0
      },
      loading: false,
      showBack: false,
      isNavigating: false,
      statusBarHeight: 0,
      customNavBarHeight: 0
    };
  },
  computed: {
    provinceOptions() {
      return [{ code: "", name: "全部省份" }, ...this.provinces];
    }
  },
  onLoad(options) {
    this.initSafeArea();
    if (options) {
      if (options.province) {
        this.currentProvince = options.province;
      }
      if (options.provinceCode) {
        this.currentProvinceCode = options.provinceCode;
      }
    }
    const pages = getCurrentPages();
    if (pages.length > 1) {
      this.showBack = true;
    }
    this.fetchProvinces();
    this.fetchData();
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
        common_vendor.index.__f__("warn", "at pages/index/index.vue:146", "获取安全区域数据失败", e);
        this.statusBarHeight = 20;
        this.customNavBarHeight = 64;
      }
    },
    goBack() {
      common_vendor.index.navigateBack();
    },
    /**
     * 加载省份列表
     */
    async fetchProvinces() {
      try {
        this.provinces = await api_positionService.positionService.getProvinces();
      } catch (e) {
        common_vendor.index.__f__("error", "at pages/index/index.vue:161", "Failed to fetch provinces", e);
      }
    },
    /**
     * 加载职位数据
     */
    async fetchData() {
      this.loading = true;
      try {
        if (this.allPositions.length === 0) {
          const params = {
            year: this.currentYear
          };
          this.allPositions = await api_positionService.positionService.getPositions(params);
        }
        this.calculateExamTypeCounts();
        this.filterPositions();
      } catch (e) {
        common_vendor.index.__f__("error", "at pages/index/index.vue:184", e);
        common_vendor.index.showToast({ title: "加载失败", icon: "none" });
      } finally {
        this.loading = false;
      }
    },
    /**
     * 计算各类型职位的数量
     */
    calculateExamTypeCounts() {
      let filteredByProvince = [...this.allPositions];
      if (this.currentProvinceCode) {
        filteredByProvince = filteredByProvince.filter((p) => p.province_code === this.currentProvinceCode);
      } else if (this.currentProvince) {
        filteredByProvince = filteredByProvince.filter((p) => p.city === this.currentProvince);
      }
      this.examTypeCounts = {
        all: filteredByProvince.length,
        provincial: filteredByProvince.filter((p) => p.position_origin === 0).length,
        enterprise: filteredByProvince.filter((p) => p.position_origin === 1).length
      };
    },
    /**
     * 在本地数据上进行筛选
     */
    filterPositions() {
      let filtered = [...this.allPositions];
      if (this.currentProvinceCode) {
        filtered = filtered.filter((p) => p.province_code === this.currentProvinceCode);
      } else if (this.currentProvince) {
        filtered = filtered.filter((p) => p.city === this.currentProvince);
      }
      if (this.searchKeyword) {
        const keyword = this.searchKeyword.toLowerCase();
        filtered = filtered.filter((p) => {
          const name = (p.position_name || "").toLowerCase();
          const unit = (p.recruit_unit || "").toLowerCase();
          const desc = (p.description || "").toLowerCase();
          const major = (p.major || "").toLowerCase();
          return name.includes(keyword) || unit.includes(keyword) || desc.includes(keyword) || major.includes(keyword);
        });
      }
      if (this.currentExamType) {
        if (this.currentExamType === "省考") {
          filtered = filtered.filter((p) => p.position_origin === 0);
        } else if (this.currentExamType === "事业编") {
          filtered = filtered.filter((p) => p.position_origin === 1);
        }
      }
      this.positions = filtered;
    },
    /**
     * 搜索事件处理
     */
    onSearch() {
      this.filterPositions();
    },
    /**
     * 切换年份筛选
     * @param {Number|String} year 年份
     */
    setYear(year) {
      this.currentYear = year;
      this.allPositions = [];
      this.fetchData();
    },
    /**
     * 切换考试类型筛选
     * @param {String} type 考试类型
     */
    setExamType(type) {
      this.currentExamType = type;
      this.filterPositions();
    },
    /**
     * 切换省份筛选（通过Picker）
     */
    onProvinceChange(e) {
      const index = e.detail.value;
      const selected = this.provinceOptions[index];
      this.currentProvinceCode = selected.code || "";
      if (selected.name === "全部省份") {
        this.currentProvince = "";
      } else {
        this.currentProvince = selected.name;
      }
      this.calculateExamTypeCounts();
      this.filterPositions();
    },
    /**
     * 跳转至详情页
     * @param {Object} position 职位对象
     */
    goToDetail(position) {
      if (this.isNavigating)
        return;
      if (!position || !position.id) {
        common_vendor.index.__f__("warn", "at pages/index/index.vue:297", "Invalid position id", position);
        return;
      }
      this.isNavigating = true;
      common_vendor.index.navigateTo({
        url: `/pages/detail/detail?id=${position.id}`,
        complete: () => {
          setTimeout(() => {
            this.isNavigating = false;
          }, 500);
        }
      });
    }
  }
};
if (!Array) {
  const _component_position_card = common_vendor.resolveComponent("position-card");
  _component_position_card();
}
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return common_vendor.e({
    a: $data.statusBarHeight + "px",
    b: $data.showBack
  }, $data.showBack ? {
    c: common_vendor.o((...args) => $options.goBack && $options.goBack(...args))
  } : {}, {
    d: common_vendor.o((...args) => $options.onSearch && $options.onSearch(...args)),
    e: $data.searchKeyword,
    f: common_vendor.o(($event) => $data.searchKeyword = $event.detail.value),
    g: common_vendor.o((...args) => $options.onSearch && $options.onSearch(...args)),
    h: common_vendor.t($data.currentProvince || "全部省份"),
    i: $options.provinceOptions,
    j: common_vendor.o((...args) => $options.onProvinceChange && $options.onProvinceChange(...args)),
    k: common_vendor.t($data.examTypeCounts.all),
    l: $data.currentExamType === "" ? 1 : "",
    m: common_vendor.o(($event) => $options.setExamType("")),
    n: common_vendor.t($data.examTypeCounts.provincial),
    o: $data.currentExamType === "省考" ? 1 : "",
    p: common_vendor.o(($event) => $options.setExamType("省考")),
    q: common_vendor.t($data.examTypeCounts.enterprise),
    r: $data.currentExamType === "事业编" ? 1 : "",
    s: common_vendor.o(($event) => $options.setExamType("事业编")),
    t: $data.loading
  }, $data.loading ? {} : $data.positions.length > 0 ? {
    w: common_vendor.f($data.positions, (item, k0, i0) => {
      return {
        a: item.id,
        b: common_vendor.o($options.goToDetail, item.id),
        c: "1cf27b2a-0-" + i0,
        d: common_vendor.p({
          position: item,
          showStatusBadge: false
        })
      };
    })
  } : {}, {
    v: $data.positions.length > 0
  });
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-1cf27b2a"]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/index/index.js.map
