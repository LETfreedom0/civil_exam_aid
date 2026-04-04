"use strict";
Object.defineProperty(exports, Symbol.toStringTag, { value: "Module" });
const common_vendor = require("./common/vendor.js");
if (!Math) {
  "./pages/preview/preview.js";
  "./pages/index/index.js";
  "./pages/detail/detail.js";
}
const _sfc_main = {
  globalData: {
    statusBarHeight: 0,
    navBarHeight: 44,
    menuButtonTop: 0,
    menuButtonHeight: 0,
    customNavBarHeight: 0
  },
  onLaunch: function() {
    common_vendor.index.__f__("log", "at App.vue:11", "App Launch");
    this.initSafeArea();
  },
  onShow: function() {
    common_vendor.index.__f__("log", "at App.vue:15", "App Show");
  },
  onHide: function() {
    common_vendor.index.__f__("log", "at App.vue:18", "App Hide");
  },
  methods: {
    initSafeArea() {
      try {
        const systemInfo = common_vendor.index.getSystemInfoSync();
        this.globalData.statusBarHeight = systemInfo.statusBarHeight || 20;
        const menuButton = common_vendor.index.getMenuButtonBoundingClientRect();
        if (menuButton) {
          this.globalData.menuButtonTop = menuButton.top;
          this.globalData.menuButtonHeight = menuButton.height;
          const menuButtonBottom = menuButton.top + menuButton.height;
          const navBarHeight = menuButtonBottom - this.globalData.statusBarHeight + (menuButton.top - this.globalData.statusBarHeight);
          this.globalData.customNavBarHeight = this.globalData.statusBarHeight + navBarHeight;
        } else {
          this.globalData.customNavBarHeight = this.globalData.statusBarHeight + 44;
        }
      } catch (e) {
        common_vendor.index.__f__("warn", "at App.vue:43", "获取安全区域失败，使用默认值", e);
        this.globalData.statusBarHeight = 20;
        this.globalData.customNavBarHeight = 64;
      }
    }
  }
};
function createApp() {
  const app = common_vendor.createSSRApp(_sfc_main);
  return {
    app
  };
}
createApp().app.mount("#app");
exports.createApp = createApp;
//# sourceMappingURL=../.sourcemap/mp-weixin/app.js.map
