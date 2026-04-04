<template>
  <view class="container">
    <view class="header-bg">
      <view class="status-bar" :style="{ height: statusBarHeight + 'px' }"></view>
      <view class="title-bar">
        <text class="title">全国残疾人公考岗位预览</text>
        <text class="subtitle">{{ currentYear }}年度招录计划</text>
      </view>
    </view>
    
    <view class="stats-box">
      <view class="stat-item">
        <text class="num">{{ totalPositions }}</text>
        <text class="label">总职位数</text>
      </view>
      <view class="divider"></view>
      <view class="stat-item">
        <text class="num">{{ totalQuota }}</text>
        <text class="label">总招录人数</text>
      </view>
    </view>

    <view class="province-section">
      <view class="section-header">
        <text class="section-title">各省份招录分布</text>
        <text class="section-more" @click="viewAll">查看全部列表 ></text>
      </view>
      
      <view class="grid">
        <view 
          class="province-card" 
          v-for="(item, index) in provinceStats" 
          :key="item.code || index"
          @click="goToProvince(item)"
        >
          <view class="card-content">
            <text class="province-name">{{ item.province }}</text>
            <view class="status-badge" :class="{ 'has-position': item.count > 0 }">
              <template v-if="item.count > 0">
                <text class="count-val">{{ item.count }}</text>
                <text class="count-unit">职位</text>
              </template>
              <template v-else>
                <text class="status-dot"></text>
                <text class="status-text">待公布</text>
              </template>
            </view>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { positionService } from '@/api/positionService.js';

export default {
  data() {
    return {
      positions: [],
      provinceStats: [],
      totalPositions: 0,
      totalQuota: 0,
      currentYear: new Date().getFullYear(),
      statusBarHeight: 0,
      customNavBarHeight: 0
    }
  },
  onLoad() {
    this.initSafeArea()
    this.loadData();
  },
  methods: {
    initSafeArea() {
      try {
        const app = getApp()
        if (app && app.globalData) {
          this.statusBarHeight = app.globalData.statusBarHeight || 20
          this.customNavBarHeight = app.globalData.customNavBarHeight || 64
        }
      } catch (e) {
        console.warn('获取安全区域数据失败', e)
        this.statusBarHeight = 20
        this.customNavBarHeight = 64
      }
    },
    /**
     * 加载并统计数据
     */
    async loadData() {
      try {
        uni.showLoading({ title: '加载中...' });
        
        // 并行获取省份列表和职位数据
        const [provinceList, data] = await Promise.all([
          positionService.getProvinces(),
          positionService.getPositions({ year: this.currentYear })
        ]);

        this.positions = data;
        
        // 统计总数
        this.totalPositions = data.length;
        this.totalQuota = data.reduce((sum, p) => sum + (Number(p.quota) || 0), 0);
        
        const normalizeProvinceName = (name) => {
          if (!name) return '';
          const s = String(name).trim();
          return s
            .replace(/特别行政区$/g, '')
            .replace(/维吾尔自治区$/g, '')
            .replace(/壮族自治区$/g, '')
            .replace(/回族自治区$/g, '')
            .replace(/自治区$/g, '')
            .replace(/省$/g, '')
            .replace(/市$/g, '');
        }

        // 初始化所有省份的统计数据（优先按 code 统计，避免 “重庆/重庆市” 等名称不一致）
        const statsMap = new Map();
        const normalizedNameToCode = new Map();
        provinceList.forEach(p => {
          const code = p.code;
          statsMap.set(code, {
            province: p.name,
            code,
            count: 0
          });
          normalizedNameToCode.set(normalizeProvinceName(p.name), code);
        });

        // 统计各省份职位数
        data.forEach(p => {
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
        
        // 转换为数组并排序：有职位的排前面（按数量降序），没职位的排后面（按代码升序）
        this.provinceStats = Array.from(statsMap.values()).sort((a, b) => {
          if (b.count !== a.count) {
            return b.count - a.count;
          }
          return Number(a.code) - Number(b.code);
        });
        
      } catch (e) {
        console.error(e);
        uni.showToast({ title: '数据加载失败', icon: 'none' });
      } finally {
        uni.hideLoading();
      }
    },
    /**
     * 跳转到指定省份的列表
     * @param {Object} item 省份对象
     */
    goToProvince(item) {
      uni.navigateTo({
        url: `/pages/index/index?province=${item.province}&provinceCode=${item.code}`
      });
    },
    /**
     * 查看全部
     */
    viewAll() {
      uni.navigateTo({
        url: '/pages/index/index'
      });
    }
  }
}
</script>

<style lang="scss" scoped>
.container {
  min-height: 100vh;
  background-color: #f5f7fa;
  padding-bottom: 40rpx;
}

.header-bg {
  background: linear-gradient(180deg, #1890ff 0%, #36cfc9 100%);
  padding: 0 40rpx 100rpx;
  color: #fff;
  
  .status-bar {
    width: 100%;
  }

  .title-bar {
    padding-top: 40rpx;
    
    .title {
      font-size: 40rpx;
      font-weight: bold;
      display: block;
      margin-bottom: 10rpx;
    }
    
    .subtitle {
      font-size: 28rpx;
      opacity: 0.9;
    }
  }
}

.stats-box {
  background: #fff;
  margin: -60rpx 30rpx 30rpx; // 负margin上移
  border-radius: 16rpx;
  padding: 40rpx;
  display: flex;
  align-items: center;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.08);
  position: relative;
  z-index: 10;
  
  .stat-item {
    flex: 1;
    text-align: center;
    
    .num {
      font-size: 48rpx;
      font-weight: bold;
      color: #333;
      display: block;
      margin-bottom: 8rpx;
    }
    
    .label {
      font-size: 24rpx;
      color: #666;
    }
  }
  
  .divider {
    width: 2rpx;
    height: 60rpx;
    background-color: #eee;
  }
}

.province-section {
  padding: 0 30rpx;
  
  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24rpx;
    
    .section-title {
      font-size: 32rpx;
      font-weight: bold;
      color: #333;
      border-left: 8rpx solid #1890ff;
      padding-left: 16rpx;
    }
    
    .section-more {
      font-size: 24rpx;
      color: #999;
    }
  }
  
  .grid {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    
    .province-card {
      width: 48%; // 两列
      background: #fff;
      border-radius: 12rpx;
      padding: 30rpx;
      margin-bottom: 24rpx;
      box-sizing: border-box;
      box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.02);
      
      &:active {
        background-color: #fafafa;
      }
      
      .card-content {
        display: flex;
        align-items: center;
        justify-content: space-between;
        width: 100%;
        
        .province-name {
          font-size: 32rpx;
          font-weight: bold;
          color: #333;
        }
        
        .status-badge {
          display: inline-flex;
          align-items: baseline;
          
          &.has-position {
            .count-val {
              font-size: 40rpx;
              font-weight: bold;
              color: #1890ff;
              margin-right: 6rpx;
              line-height: 1;
            }
            .count-unit {
              font-size: 24rpx;
              color: #666;
            }
          }
          
          &:not(.has-position) {
            display: flex;
            align-items: center;
            background: #f0f2f5;
            padding: 4rpx 12rpx;
            border-radius: 6rpx;
            
            .status-dot {
              width: 10rpx;
              height: 10rpx;
              background: #ccc;
              border-radius: 50%;
              margin-right: 8rpx;
            }
            .status-text {
              font-size: 24rpx;
              color: #999;
            }
          }
        }
      }
    }
  }
}
</style>
