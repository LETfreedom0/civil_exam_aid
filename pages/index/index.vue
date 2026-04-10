<template>
  <view class="container">
    <view class="header">
      <view class="status-bar" :style="{ height: statusBarHeight + 'px' }"></view>
      <view class="title-bar">
        <text v-if="showBack" class="back-btn" @click="goBack">❮</text>
        <text class="app-title">公考岗位查询</text>
      </view>
      <view class="search-bar">
        <input 
          class="search-input" 
          type="text" 
          v-model="searchKeyword" 
          placeholder="搜索职位/单位/专业" 
          confirm-type="search"
          @confirm="onSearch"
        />
        <view class="search-btn" @click="onSearch">搜索</view>
      </view>
      <view class="filters">
        <view class="province-selector">
          <picker 
            mode="selector" 
            :range="provinceOptions" 
            range-key="name"
            @change="onProvinceChange"
          >
            <view class="picker-trigger">
              <text>{{ currentProvince || '全部省份' }}</text>
              <text class="picker-arrow">▼</text>
            </view>
          </picker>
        </view>
        
        <view class="filter-scroll">
          <view 
            class="filter-item" 
            :class="{ 'active': currentExamType === '' }"
            @click="setExamType('')"
          >
            全部
            <view class="count-badge">{{ examTypeCounts.all }}</view>
          </view>
          <view 
            class="filter-item" 
            :class="{ 'active': currentExamType === '省考' }"
            @click="setExamType('省考')"
          >
            省考
            <view class="count-badge">{{ examTypeCounts.provincial }}</view>
          </view>
          <view 
            class="filter-item" 
            :class="{ 'active': currentExamType === '事业编' }"
            @click="setExamType('事业编')"
          >
            事业编
            <view class="count-badge">{{ examTypeCounts.enterprise }}</view>
          </view>
        </view>
      </view>
    </view>

    <view class="list-container">
      <view v-if="loading" class="loading">加载中...</view>
      <view v-else-if="positions.length > 0">
        <position-card 
          v-for="item in positions" 
          :key="item.id" 
          :position="item"
          :showStatusBadge="true"
          @click="goToDetail"
        />
      </view>
      <view v-else class="empty">
        <text>暂无相关职位</text>
      </view>
    </view>
  </view>
</template>

<script>
import { positionService } from '@/api/positionService.js';
import PositionCard from '@/components/PositionCard.vue';

export default {
  components: {
    PositionCard
  },
  data() {
    return {
      searchKeyword: '',
      currentYear: 2026,
      currentProvince: '',
      currentProvinceCode: '',
      currentExamType: '',
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
    }
  },
  computed: {
    provinceOptions() {
      return [{code: '', name: '全部省份'}, ...this.provinces];
    }
  },
  onLoad(options) {
    this.initSafeArea()
    
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
    goBack() {
      uni.navigateBack();
    },
    /**
     * 加载省份列表
     */
    async fetchProvinces() {
      try {
        this.provinces = await positionService.getProvinces();
      } catch (e) {
        console.error('Failed to fetch provinces', e);
      }
    },
    /**
     * 加载职位数据
     */
    async fetchData() {
      this.loading = true;
      try {
        // 首次加载时从后端获取所有数据
        if (this.allPositions.length === 0) {
          const params = {
            year: this.currentYear
          };
          this.allPositions = await positionService.getPositions(params);
        }
        
        // 计算各类型职位的数量
        this.calculateExamTypeCounts();
        
        // 在本地数据上进行筛选
        this.filterPositions();
      } catch (e) {
        console.error(e);
        uni.showToast({ title: '加载失败', icon: 'none' });
      } finally {
        this.loading = false;
      }
    },
    /**
     * 计算各类型职位的数量
     */
    calculateExamTypeCounts() {
      // 首先获取当前省份筛选后的所有数据
      let filteredByProvince = [...this.allPositions];
      
      // 过滤掉过时的卡片（年份小于当前年份）
      const currentYear = new Date().getFullYear();
      filteredByProvince = filteredByProvince.filter(p => p.year >= currentYear);
      
      if (this.currentProvinceCode) {
        filteredByProvince = filteredByProvince.filter(p => p.province_code === this.currentProvinceCode);
      } else if (this.currentProvince) {
        filteredByProvince = filteredByProvince.filter(p => p.city === this.currentProvince);
      }
      
      // 计算各类型的数量
      this.examTypeCounts = {
        all: filteredByProvince.length,
        provincial: filteredByProvince.filter(p => p.position_origin === 0).length,
        enterprise: filteredByProvince.filter(p => p.position_origin === 1).length
      };
    },
    /**
     * 在本地数据上进行筛选
     */
    filterPositions() {
      let filtered = [...this.allPositions];
      
      // 过滤掉过时的卡片（年份小于当前年份）
      const currentYear = new Date().getFullYear();
      filtered = filtered.filter(p => p.year >= currentYear);
      
      // 省份筛选
      if (this.currentProvinceCode) {
        filtered = filtered.filter(p => p.province_code === this.currentProvinceCode);
      } else if (this.currentProvince) {
        filtered = filtered.filter(p => p.city === this.currentProvince);
      }
      
      // 关键词筛选
      if (this.searchKeyword) {
        const keyword = this.searchKeyword.toLowerCase();
        filtered = filtered.filter(p => {
          const name = (p.position_name || '').toLowerCase();
          const unit = (p.recruit_unit || '').toLowerCase();
          const desc = (p.description || '').toLowerCase();
          const major = (p.major || '').toLowerCase();
          return name.includes(keyword) || unit.includes(keyword) || desc.includes(keyword) || major.includes(keyword);
        });
      }
      
      // 考试类型筛选
      if (this.currentExamType) {
        if (this.currentExamType === '省考') {
          filtered = filtered.filter(p => p.position_origin === 0);
        } else if (this.currentExamType === '事业编') {
          filtered = filtered.filter(p => p.position_origin === 1);
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
      // 年份改变时需要重新从后端获取数据
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
      
      this.currentProvinceCode = selected.code || '';
      
      if (selected.name === '全部省份') {
        this.currentProvince = '';
      } else {
        this.currentProvince = selected.name;
      }
      
      // 重新计算各类型职位的数量
      this.calculateExamTypeCounts();
      
      this.filterPositions();
    },
    /**
     * 跳转至详情页
     * @param {Object} position 职位对象
     */
    goToDetail(position) {
      if (this.isNavigating) return;
      
      if (!position || !position.id) {
        console.warn('Invalid position id', position);
        return;
      }

      this.isNavigating = true;
      uni.navigateTo({
        url: `/pages/detail/detail?id=${position.id}`,
        complete: () => {
          setTimeout(() => {
            this.isNavigating = false;
          }, 500);
        }
      });
    }
  }
}
</script>

<style lang="scss" scoped>
.container {
  min-height: 100vh;
  background-color: #f5f7fa;
}

.header {
  background-color: #1890ff;
  padding: 0 20rpx 30rpx;
  position: sticky;
  top: 0;
  z-index: 100;
  
  .status-bar {
    width: 100%;
  }

  .title-bar {
    height: 88rpx;
    display: flex;
    align-items: center;
    margin-bottom: 10rpx;
    padding-top: 10rpx;
    
    .back-btn {
      color: #fff;
      font-size: 36rpx;
      margin-right: 20rpx;
      padding: 0 10rpx;
      font-weight: bold;
    }

    .app-title {
      font-size: 36rpx;
      font-weight: bold;
      color: #fff;
    }
  }
  
  .search-bar {
    display: flex;
    background: #fff;
    border-radius: 40rpx;
    padding: 10rpx 20rpx;
    align-items: center;
    margin-bottom: 20rpx;
    
    .search-input {
      flex: 1;
      height: 60rpx;
      font-size: 28rpx;
      margin-right: 20rpx;
    }
    
    .search-btn {
      color: #1890ff;
      font-weight: bold;
      font-size: 28rpx;
      padding: 10rpx 20rpx;
    }
  }
  
  .filters {
    display: flex;
    align-items: center;
    justify-content: flex-start;
    
    .province-selector {
      margin-right: 20rpx;
      
      .picker-trigger {
        display: flex;
        align-items: center;
        background: rgba(255, 255, 255, 0.2);
        padding: 8rpx 24rpx;
        border-radius: 30rpx;
        color: #fff;
        font-size: 26rpx;
        white-space: nowrap;
        
        .picker-arrow {
          font-size: 20rpx;
          margin-left: 8rpx;
          opacity: 0.8;
        }
      }
    }
    
    .filter-scroll {
      flex: 1;
      white-space: nowrap;
      
      .filter-item {
        display: inline-flex;
        align-items: center;
        padding: 8rpx 24rpx;
        background: rgba(255, 255, 255, 0.2);
        color: #fff;
        border-radius: 30rpx;
        margin-right: 16rpx;
        font-size: 26rpx;
        
        &.active {
          background: #fff;
          color: #1890ff;
          font-weight: bold;
        }
        
        .count-badge {
          margin-left: 8rpx;
          background: rgba(255, 255, 255, 0.3);
          color: #fff;
          padding: 2rpx 10rpx;
          border-radius: 12rpx;
          font-size: 20rpx;
          font-weight: normal;
        }
        
        &.active .count-badge {
          background: rgba(24, 144, 255, 0.2);
          color: #1890ff;
        }
      }
    }
  }
}

.list-container {
  padding: 20rpx;
}

.loading, .empty {
  text-align: center;
  padding: 100rpx 0;
  color: #999;
}
</style>
