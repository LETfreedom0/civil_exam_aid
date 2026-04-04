<template>
  <view class="card" @click="onClick">
    <view class="header">
      <text class="title">{{ position.position_name }}</text>
      <text class="quota">{{ position.quota }}人</text>
    </view>
    <view class="sub-header">
      <text class="unit" v-if="position.recruit_unit">{{ position.recruit_unit }}</text>
      <text class="divider" v-if="position.recruit_unit && position.region_dept">|</text>
      <text class="region" v-if="position.region_dept">{{ position.region_dept }}</text>
    </view>
    <view class="tags" v-if="originLabel || position.education || position.degree">
      <text class="tag" :class="originClass" v-if="originLabel">{{ originLabel }}</text>
      <text class="tag" v-if="position.education">{{ position.education }}</text>
      <text class="tag" v-if="position.degree">{{ position.degree }}</text>
    </view>
    <view class="footer" v-if="position.other_requirements">
      <text class="requirement">残疾要求: {{ formatRequirement(position.other_requirements) }}</text>
    </view>
    <view class="status-badge" :class="statusClass" v-if="showStatusBadge && statusLabel">{{ statusLabel }}</view>
  </view>
</template>

<script>
export default {
  name: 'PositionCard',
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
      const v = this.position?.position_origin;
      if (v === 0) return '省考';
      if (v === 1) return '事业编';
      if (v === undefined || v === null) return '';
      return '其他';
    },
    /**
     * 计算岗位来源标签样式类名
     */
    originClass() {
      const v = this.position?.position_origin;
      if (v === 0) return 'origin-provincial';
      if (v === 1) return 'origin-enterprise';
      return 'origin-other';
    },
    /**
     * 计算岗位状态标签文本
     * 基于年份粗略判断：今年=报名中，未来=待开始，过去=已结束
     */
    statusLabel() {
      const y = this.position?.year;
      if (typeof y !== 'number') return '';
      const currentYear = new Date().getFullYear();
      if (y > currentYear) return '待开始';
      if (y === currentYear) return '报名中';
      return '已结束';
    },
    /**
     * 计算岗位状态标签样式类名
     */
    statusClass() {
      const y = this.position?.year;
      const currentYear = new Date().getFullYear();
      if (typeof y !== 'number') return 'status-default';
      if (y > currentYear) return 'status-upcoming';
      if (y === currentYear) return 'status-running';
      return 'status-finished';
    }
  },
  methods: {
    /**
     * 卡片点击事件：向父组件派发点击当前职位数据
     */
    onClick() {
      this.$emit('click', this.position);
    },
    /**
     * 截断“其他要求”文本，避免过长影响展示
     */
    formatRequirement(text) {
      if (!text) return '';
      return text.length > 15 ? text.substring(0, 15) + '...' : text;
    }
  }
}
</script>

<style lang="scss" scoped>
.card {
  background-color: #ffffff;
  border-radius: 12rpx;
  padding: 24rpx;
  margin-bottom: 20rpx;
  box-shadow: 0 2rpx 10rpx rgba(0, 0, 0, 0.05);
  border: 1rpx solid #f0f0f0;
  position: relative;
  
  &:active {
    background-color: #fafafa;
  }
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12rpx;
  
  .title {
    font-size: 32rpx;
    font-weight: bold;
    color: #333;
  }
  
  .quota {
    font-size: 28rpx;
    color: #007aff;
    font-weight: bold;
    background-color: rgba(0, 122, 255, 0.1);
    padding: 4rpx 12rpx;
    border-radius: 8rpx;
  }
}

.sub-header {
  display: flex;
  align-items: center;
  margin-bottom: 16rpx;
  
  .unit, .region {
    font-size: 26rpx;
    color: #666;
  }
  
  .divider {
    margin: 0 10rpx;
    color: #ddd;
    font-size: 24rpx;
  }
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-bottom: 16rpx;
  
  .tag {
    font-size: 24rpx;
    color: #555;
    background-color: #f5f5f5;
    padding: 4rpx 12rpx;
    border-radius: 6rpx;
  }
  .origin-provincial {
    color: #096dd9;
    background-color: #e6f7ff;
    border: 1rpx solid #91d5ff;
  }
  .origin-enterprise {
    color: #d46b08;
    background-color: #fff7e6;
    border: 1rpx solid #ffd591;
  }
  .origin-other {
    color: #595959;
    background-color: #fafafa;
    border: 1rpx solid #d9d9d9;
  }
}

.footer {
  border-top: 1rpx solid #eee;
  padding-top: 12rpx;
  
  .requirement {
    font-size: 24rpx;
    color: #999;
  }
}

.status-badge {
  position: absolute;
  right: 16rpx;
  bottom: 16rpx;
  font-size: 22rpx;
  padding: 6rpx 10rpx;
  border-radius: 6rpx;
  background: rgba(0, 0, 0, 0.04);
  color: #666;
  border: 1rpx solid rgba(0, 0, 0, 0.08);
  z-index: 1;
}
.status-running { background: rgba(82, 196, 26, 0.12); color: #245a1a; border-color: rgba(82, 196, 26, 0.25); }
.status-upcoming { background: rgba(250, 140, 22, 0.12); color: #6a3a00; border-color: rgba(250, 140, 22, 0.25); }
.status-finished { background: rgba(0, 0, 0, 0.04); color: #8c8c8c; border-color: rgba(0, 0, 0, 0.10); }
.status-default { background: rgba(0, 0, 0, 0.04); color: #666; border-color: rgba(0, 0, 0, 0.08); }
</style>
