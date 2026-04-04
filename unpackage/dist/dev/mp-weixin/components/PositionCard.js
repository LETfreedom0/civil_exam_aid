"use strict";
const common_vendor = require("../common/vendor.js");
const _sfc_main = {
  name: "PositionCard",
  props: {
    position: {
      type: Object,
      required: true
    },
    showStatusBadge: {
      type: Boolean,
      default: false
    }
  },
  computed: {
    /**
     * 计算岗位来源标签文本
     * 0=省考岗位，1=事业单位岗位，其他=其他岗位；无值返回空
     */
    originLabel() {
      var _a;
      const v = (_a = this.position) == null ? void 0 : _a.position_origin;
      if (v === 0)
        return "省考";
      if (v === 1)
        return "事业编";
      if (v === void 0 || v === null)
        return "";
      return "其他";
    },
    /**
     * 计算岗位来源标签样式类名
     */
    originClass() {
      var _a;
      const v = (_a = this.position) == null ? void 0 : _a.position_origin;
      if (v === 0)
        return "origin-provincial";
      if (v === 1)
        return "origin-enterprise";
      return "origin-other";
    },
    /**
     * 计算岗位状态标签文本
     * 基于年份粗略判断：今年=报名中，未来=待开始，过去=已结束
     */
    statusLabel() {
      var _a;
      const y = (_a = this.position) == null ? void 0 : _a.year;
      if (typeof y !== "number")
        return "";
      const currentYear = (/* @__PURE__ */ new Date()).getFullYear();
      if (y > currentYear)
        return "待开始";
      if (y === currentYear)
        return "报名中";
      return "已结束";
    },
    /**
     * 计算岗位状态标签样式类名
     */
    statusClass() {
      var _a;
      const y = (_a = this.position) == null ? void 0 : _a.year;
      const currentYear = (/* @__PURE__ */ new Date()).getFullYear();
      if (typeof y !== "number")
        return "status-default";
      if (y > currentYear)
        return "status-upcoming";
      if (y === currentYear)
        return "status-running";
      return "status-finished";
    }
  },
  methods: {
    /**
     * 卡片点击事件：向父组件派发点击当前职位数据
     */
    onClick() {
      this.$emit("click", this.position);
    },
    /**
     * 截断“其他要求”文本，避免过长影响展示
     */
    formatRequirement(text) {
      if (!text)
        return "";
      return text.length > 15 ? text.substring(0, 15) + "..." : text;
    }
  }
};
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return common_vendor.e({
    a: common_vendor.t($props.position.position_name),
    b: common_vendor.t($props.position.quota),
    c: $props.position.recruit_unit
  }, $props.position.recruit_unit ? {
    d: common_vendor.t($props.position.recruit_unit)
  } : {}, {
    e: $props.position.recruit_unit && $props.position.region_dept
  }, $props.position.recruit_unit && $props.position.region_dept ? {} : {}, {
    f: $props.position.region_dept
  }, $props.position.region_dept ? {
    g: common_vendor.t($props.position.region_dept)
  } : {}, {
    h: $options.originLabel || $props.position.education || $props.position.degree
  }, $options.originLabel || $props.position.education || $props.position.degree ? common_vendor.e({
    i: $options.originLabel
  }, $options.originLabel ? {
    j: common_vendor.t($options.originLabel),
    k: common_vendor.n($options.originClass)
  } : {}, {
    l: $props.position.education
  }, $props.position.education ? {
    m: common_vendor.t($props.position.education)
  } : {}, {
    n: $props.position.degree
  }, $props.position.degree ? {
    o: common_vendor.t($props.position.degree)
  } : {}) : {}, {
    p: $props.position.other_requirements
  }, $props.position.other_requirements ? {
    q: common_vendor.t($options.formatRequirement($props.position.other_requirements))
  } : {}, {
    r: $props.showStatusBadge && $options.statusLabel
  }, $props.showStatusBadge && $options.statusLabel ? {
    s: common_vendor.t($options.statusLabel),
    t: common_vendor.n($options.statusClass)
  } : {}, {
    v: common_vendor.o((...args) => $options.onClick && $options.onClick(...args))
  });
}
const Component = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-4d144a3a"]]);
wx.createComponent(Component);
//# sourceMappingURL=../../.sourcemap/mp-weixin/components/PositionCard.js.map
