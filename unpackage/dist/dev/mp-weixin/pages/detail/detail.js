"use strict";
const common_vendor = require("../../common/vendor.js");
const api_positionService = require("../../api/positionService.js");
const _sfc_main = {
  data() {
    return {
      position: null,
      timeline: null,
      showTimelineModal: false,
      isLoading: true,
      errorMsg: "",
      currentId: "",
      showReportModal: false,
      reportType: "",
      reportDesc: "",
      submitting: false,
      canReport: true
    };
  },
  onLoad(options) {
    const today = (/* @__PURE__ */ new Date()).toISOString().split("T")[0];
    const lastReportDate = common_vendor.index.getStorageSync("lastReportDate");
    if (lastReportDate === today) {
      this.canReport = false;
    }
    if (options.id) {
      this.currentId = options.id;
      this.loadData(options.id);
    } else {
      this.isLoading = false;
      this.errorMsg = "参数错误：未提供职位ID";
    }
  },
  computed: {
    /**
     * 计算岗位来源标签文本
     * 0=省考，1=事业，其它=其他；无值返回空
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
    timelineSteps() {
      if (!this.timeline)
        return [];
      const steps = [];
      const now = /* @__PURE__ */ new Date();
      const today = now.toISOString().split("T")[0];
      const addStep = (title, dateKey, endDateKey = null) => {
        if (!this.timeline[dateKey])
          return;
        let dateStr = this.timeline[dateKey];
        let status = "wait";
        let fullDateStr = dateStr;
        if (endDateKey && this.timeline[endDateKey]) {
          fullDateStr = `${dateStr} 至 ${this.timeline[endDateKey]}`;
          if (today > this.timeline[endDateKey]) {
            status = "finished";
          } else if (today >= dateStr) {
            status = "process";
          }
        } else {
          if (today > dateStr) {
            status = "finished";
          } else if (today === dateStr) {
            status = "process";
          }
        }
        steps.push({
          title,
          date: fullDateStr,
          status,
          rawDate: dateStr
        });
      };
      addStep("报名", "signup_start", "signup_end");
      addStep("缴费", "signup_end", "payment_end");
      addStep("打印准考证", "admit_card_start");
      addStep("笔试", "exam_date");
      addStep("查分", "score_date");
      addStep("面试", "interview_date_start");
      return steps;
    },
    currentStatusSimple() {
      if (!this.timelineSteps || this.timelineSteps.length === 0)
        return "";
      const activeStep = this.timelineSteps.find((s) => s.status === "process");
      if (activeStep) {
        return `${activeStep.title}中 >`;
      }
      const nextStep = this.timelineSteps.find((s) => s.status === "wait");
      if (nextStep) {
        let date = nextStep.rawDate;
        if (date && date.includes("-")) {
          date = date.substring(5);
        }
        return `待${nextStep.title} ${date} >`;
      }
      return "已结束 >";
    },
    phoneList() {
      const list = [];
      if (this.position) {
        if (this.position.phone1 && this.position.phone1.trim()) {
          list.push(this.position.phone1.trim());
        }
        if (this.position.phone2 && this.position.phone2.trim()) {
          list.push(this.position.phone2.trim());
        }
      }
      return list;
    },
    formattedMaxAge() {
      if (!this.position || !this.position.max_age)
        return "";
      const age = String(this.position.max_age).trim();
      if (age.includes("以下") || age.includes("以内") || age.includes("最大") || age.includes("不超过") || age.includes("以上") || age.includes("-") || age.includes("至") || age.includes("≤")) {
        return age;
      }
      const match = age.match(/(\d+)/);
      if (match) {
        return `≤${match[1]}周岁`;
      }
      return age;
    }
  },
  methods: {
    /**
     * 根据ID加载职位详情
     * @param {String} id 职位ID
     */
    async loadData(id) {
      this.isLoading = true;
      this.errorMsg = "";
      try {
        common_vendor.index.__f__("log", "at pages/detail/detail.vue:475", "正在加载职位详情，ID:", id);
        this.position = await api_positionService.positionService.getPositionById(id);
        common_vendor.index.__f__("log", "at pages/detail/detail.vue:477", "职位详情加载成功:", this.position);
        if (this.position) {
          if (this.position.province_code && this.position.year) {
            this.timeline = await api_positionService.positionService.getExamTimeline(this.position.province_code, this.position.year);
          }
        } else {
          this.errorMsg = "未找到该职位信息";
        }
      } catch (e) {
        common_vendor.index.__f__("error", "at pages/detail/detail.vue:488", "加载职位详情失败:", e);
        this.errorMsg = "加载失败，请检查网络或稍后重试";
      } finally {
        this.isLoading = false;
      }
    },
    retryLoad() {
      if (this.currentId) {
        this.loadData(this.currentId);
      }
    },
    /**
     * 拨打咨询电话
     */
    makeCall(phoneNumber) {
      if (phoneNumber) {
        common_vendor.index.makePhoneCall({
          phoneNumber
        });
      }
    },
    /**
     * 触发分享逻辑（非微信小程序平台）
     * - H5：优先使用 Web Share API，回退为复制链接
     * - App：可根据需要扩展为 uni.share
     */
    async sharePosition() {
      var _a, _b;
      try {
        const title = ((_a = this.position) == null ? void 0 : _a.position_name) || "职位详情";
        const id = this.currentId || ((_b = this.position) == null ? void 0 : _b.id);
        const origin = typeof location !== "undefined" ? location.origin : "";
        const url = `${origin}/#/pages/detail/detail?id=${id}`;
        if (typeof navigator !== "undefined" && navigator.share) {
          await navigator.share({
            title,
            text: `查看职位：${title}`,
            url
          });
          common_vendor.index.showToast({ title: "已分享", icon: "success" });
          return;
        }
        await this.copyToClipboard(url);
        common_vendor.index.showToast({ title: "链接已复制", icon: "success" });
      } catch (e) {
        common_vendor.index.__f__("error", "at pages/detail/detail.vue:535", "分享失败", e);
        common_vendor.index.showToast({ title: "分享失败", icon: "none" });
      }
    },
    /**
     * 复制文本到剪贴板（H5 回退方案）
     * @param {String} text 需要复制的文本
     */
    async copyToClipboard(text) {
      if (typeof navigator !== "undefined" && navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(text);
        return;
      }
      if (typeof document !== "undefined") {
        const input = document.createElement("input");
        input.value = text;
        document.body.appendChild(input);
        input.select();
        try {
          document.execCommand("copy");
        } finally {
          document.body.removeChild(input);
        }
      }
    },
    async submitReport() {
      var _a;
      if (!this.reportType) {
        common_vendor.index.showToast({ title: "请先选择问题类型", icon: "none", duration: 2e3 });
        return;
      }
      if (!this.reportDesc || this.reportDesc.trim() === "") {
        common_vendor.index.showToast({ title: "请填写补充说明", icon: "none", duration: 2e3 });
        return;
      }
      const today = (/* @__PURE__ */ new Date()).toISOString().split("T")[0];
      const lastReportDate = common_vendor.index.getStorageSync("lastReportDate");
      if (lastReportDate === today) {
        common_vendor.index.showToast({ title: "您今天已经提交过反馈，请明天再试", icon: "none", duration: 2e3 });
        return;
      }
      this.submitting = true;
      try {
        const reportData = {
          position_id: this.currentId,
          position_name: (_a = this.position) == null ? void 0 : _a.position_name,
          report_type: this.reportType,
          description: this.reportDesc
        };
        common_vendor.index.__f__("log", "at pages/detail/detail.vue:590", "提交报错反馈:", reportData);
        await api_positionService.positionService.submitReport(reportData);
        const today2 = (/* @__PURE__ */ new Date()).toISOString().split("T")[0];
        common_vendor.index.setStorageSync("lastReportDate", today2);
        this.canReport = false;
        this.showReportModal = false;
        this.reportType = "";
        this.reportDesc = "";
        common_vendor.index.showModal({
          title: "提交成功",
          content: "感谢您的反馈，我们会尽快核实处理！",
          showCancel: false,
          confirmText: "知道了",
          confirmColor: "#1890ff",
          success: function(res) {
          }
        });
      } catch (e) {
        common_vendor.index.__f__("error", "at pages/detail/detail.vue:617", "提交反馈失败:", e);
        common_vendor.index.showToast({ title: "提交失败，请稍后重试", icon: "none", duration: 2e3 });
      } finally {
        this.submitting = false;
      }
    }
  },
  /**
   * 微信小程序分享消息配置
   * 控制分享标题、路径与（可选）图片
   */
  onShareAppMessage() {
    var _a, _b;
    const title = ((_a = this.position) == null ? void 0 : _a.position_name) || "职位详情";
    const id = this.currentId || ((_b = this.position) == null ? void 0 : _b.id);
    return {
      title: `助残公考｜${title}`,
      path: `/pages/detail/detail?id=${id}`
    };
  },
  /**
   * 微信朋友圈分享配置
   * 使用 query 传递参数
   */
  onShareTimeline() {
    var _a, _b;
    const title = ((_a = this.position) == null ? void 0 : _a.position_name) || "职位详情";
    const id = this.currentId || ((_b = this.position) == null ? void 0 : _b.id);
    return {
      title: `助残公考｜${title}`,
      query: `id=${id}`
    };
  }
};
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  var _a, _b, _c, _d, _e, _f, _g, _h;
  return common_vendor.e({
    a: $data.position
  }, $data.position ? common_vendor.e({
    b: common_vendor.t($data.position.position_name),
    c: !$data.canReport ? 1 : "",
    d: common_vendor.o(($event) => $data.canReport && ($data.showReportModal = true)),
    e: $options.originLabel && ((_a = $data.position) == null ? void 0 : _a.position_origin) === 0
  }, $options.originLabel && ((_b = $data.position) == null ? void 0 : _b.position_origin) === 0 ? {
    f: common_vendor.t($options.originLabel)
  } : {}, {
    g: $options.originLabel && ((_c = $data.position) == null ? void 0 : _c.position_origin) === 1
  }, $options.originLabel && ((_d = $data.position) == null ? void 0 : _d.position_origin) === 1 ? {
    h: common_vendor.t($options.originLabel)
  } : {}, {
    i: $options.originLabel && ((_e = $data.position) == null ? void 0 : _e.position_origin) !== 0 && ((_f = $data.position) == null ? void 0 : _f.position_origin) !== 1
  }, $options.originLabel && ((_g = $data.position) == null ? void 0 : _g.position_origin) !== 0 && ((_h = $data.position) == null ? void 0 : _h.position_origin) !== 1 ? {
    j: common_vendor.t($options.originLabel)
  } : {}, {
    k: $data.position.position_type
  }, $data.position.position_type ? {
    l: common_vendor.t($data.position.position_type)
  } : {}, {
    m: $data.position.quota
  }, $data.position.quota ? {
    n: common_vendor.t($data.position.quota)
  } : {}, {
    o: $data.position.year
  }, $data.position.year ? {
    p: common_vendor.t($data.position.year)
  } : {}, {
    q: $data.position.position_code
  }, $data.position.position_code ? {
    r: common_vendor.t($data.position.position_code)
  } : {}, {
    s: $data.position.region_dept
  }, $data.position.region_dept ? {
    t: common_vendor.t($data.position.region_dept)
  } : {}, {
    v: $data.position.exam_region
  }, $data.position.exam_region ? {
    w: common_vendor.t($data.position.exam_region)
  } : {}, {
    x: $data.position.recruit_unit
  }, $data.position.recruit_unit ? {
    y: common_vendor.t($data.position.recruit_unit)
  } : {}, {
    z: $data.position.unit_level
  }, $data.position.unit_level ? {
    A: common_vendor.t($data.position.unit_level)
  } : {}, {
    B: $data.position.position_nature
  }, $data.position.position_nature ? {
    C: common_vendor.t($data.position.position_nature)
  } : {}, {
    D: $data.position.rank_level
  }, $data.position.rank_level ? {
    E: common_vendor.t($data.position.rank_level)
  } : {}, {
    F: $options.phoneList.length > 0
  }, $options.phoneList.length > 0 ? {
    G: common_vendor.f($options.phoneList, (phone, index, i0) => {
      return {
        a: common_vendor.t(phone),
        b: index,
        c: common_vendor.o(($event) => $options.makeCall(phone), index)
      };
    })
  } : {}, {
    H: $data.position.education
  }, $data.position.education ? {
    I: common_vendor.t($data.position.education)
  } : {}, {
    J: $data.position.degree
  }, $data.position.degree ? {
    K: common_vendor.t($data.position.degree)
  } : {}, {
    L: $data.position.major
  }, $data.position.major ? {
    M: common_vendor.t($data.position.major)
  } : {}, {
    N: $data.position.grassroots_exp
  }, $data.position.grassroots_exp ? {
    O: common_vendor.t($data.position.grassroots_exp)
  } : {}, {
    P: $data.position.political_status
  }, $data.position.political_status ? {
    Q: common_vendor.t($data.position.political_status)
  } : {}, {
    R: $data.position.candidate_identity
  }, $data.position.candidate_identity ? {
    S: common_vendor.t($data.position.candidate_identity)
  } : {}, {
    T: $data.position.gender
  }, $data.position.gender ? {
    U: common_vendor.t($data.position.gender)
  } : {}, {
    V: $options.formattedMaxAge
  }, $options.formattedMaxAge ? {
    W: common_vendor.t($options.formattedMaxAge)
  } : {}, {
    X: $data.position.domicile
  }, $data.position.domicile ? {
    Y: common_vendor.t($data.position.domicile)
  } : {}, {
    Z: $data.position.certification
  }, $data.position.certification ? {
    aa: common_vendor.t($data.position.certification)
  } : {}, {
    ab: $data.position.min_service_years
  }, $data.position.min_service_years ? {
    ac: common_vendor.t($data.position.min_service_years)
  } : {}, {
    ad: $data.position.fresh_grad
  }, $data.position.fresh_grad ? {
    ae: common_vendor.t($data.position.fresh_grad)
  } : {}, {
    af: $data.position.other_requirements
  }, $data.position.other_requirements ? {
    ag: common_vendor.t($data.position.other_requirements)
  } : {}, {
    ah: $data.position.exam_ratio
  }, $data.position.exam_ratio ? {
    ai: common_vendor.t($data.position.exam_ratio)
  } : {}, {
    aj: $data.position.exam_subjects
  }, $data.position.exam_subjects ? {
    ak: common_vendor.t($data.position.exam_subjects)
  } : {}, {
    al: $data.position.exam_type
  }, $data.position.exam_type ? {
    am: common_vendor.t($data.position.exam_type)
  } : {}, {
    an: $data.position.interview_ratio
  }, $data.position.interview_ratio ? {
    ao: common_vendor.t($data.position.interview_ratio)
  } : {}, {
    ap: $data.position.inspection_ratio
  }, $data.position.inspection_ratio ? {
    aq: common_vendor.t($data.position.inspection_ratio)
  } : {}, {
    ar: $data.position.physical_test
  }, $data.position.physical_test ? {
    as: common_vendor.t($data.position.physical_test)
  } : {}, {
    at: $data.position.physical_test_standards
  }, $data.position.physical_test_standards ? {
    av: common_vendor.t($data.position.physical_test_standards)
  } : {}, {
    aw: $data.position.medical_test_standards
  }, $data.position.medical_test_standards ? {
    ax: common_vendor.t($data.position.medical_test_standards)
  } : {}, {
    ay: $data.position.description
  }, $data.position.description ? {
    az: common_vendor.t($data.position.description)
  } : {}) : {}, {
    aA: $data.showTimelineModal
  }, $data.showTimelineModal ? {
    aB: common_vendor.o(($event) => $data.showTimelineModal = false),
    aC: common_vendor.f($options.timelineSteps, (step, index, i0) => {
      return common_vendor.e({
        a: step.status === "finished"
      }, step.status === "finished" ? {} : step.status === "process" ? {} : {
        c: common_vendor.t(index + 1)
      }, {
        b: step.status === "process",
        d: common_vendor.t(step.title),
        e: common_vendor.t(step.date),
        f: index < $options.timelineSteps.length - 1
      }, index < $options.timelineSteps.length - 1 ? {} : {}, {
        g: index,
        h: common_vendor.n(step.status)
      });
    }),
    aD: common_vendor.o(() => {
    }),
    aE: common_vendor.o(($event) => $data.showTimelineModal = false)
  } : {}, {
    aF: $data.showReportModal
  }, $data.showReportModal ? common_vendor.e({
    aG: common_vendor.o(($event) => $data.showReportModal = false),
    aH: $data.reportType === "info_error" ? 1 : "",
    aI: common_vendor.o(($event) => $data.reportType = "info_error"),
    aJ: $data.reportType === "expired" ? 1 : "",
    aK: common_vendor.o(($event) => $data.reportType = "expired"),
    aL: $data.reportType === "missing" ? 1 : "",
    aM: common_vendor.o(($event) => $data.reportType = "missing"),
    aN: $data.reportType === "other" ? 1 : "",
    aO: common_vendor.o(($event) => $data.reportType = "other"),
    aP: common_vendor.t($data.reportDesc.length),
    aQ: $data.reportDesc,
    aR: common_vendor.o(($event) => $data.reportDesc = $event.detail.value),
    aS: $data.submitting
  }, $data.submitting ? {} : !$data.reportType ? {} : {}, {
    aT: !$data.reportType,
    aU: !$data.reportType ? 1 : "",
    aV: !$data.reportType || $data.submitting,
    aW: common_vendor.o((...args) => $options.submitReport && $options.submitReport(...args)),
    aX: common_vendor.o(() => {
    }),
    aY: common_vendor.o(($event) => $data.showReportModal = false)
  }) : {});
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-eca06f3c"]]);
_sfc_main.__runtimeHooks = 6;
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/detail/detail.js.map
