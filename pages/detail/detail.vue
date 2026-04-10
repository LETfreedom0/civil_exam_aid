<template>
  <view class="container">
    <view v-if="position" class="content">
      <view class="header-section">
        <view class="title-row">
          <text class="title">{{ position.position_name }}</text>
          <view class="action-area">
            <view class="report-btn" :class="{ disabled: !canReport }" @click="canReport && (showReportModal = true)">
              <image class="report-icon" src="/static/icons/report.png" mode="aspectFill"></image>
              <text class="report-text">报错</text>
            </view>
            <view class="share-area">
              <!-- #ifdef MP-WEIXIN -->
              <button class="share-btn" open-type="share">
                <image class="share-icon" src="/static/icons/share.png" mode="aspectFill"></image>
                <text class="share-label">分享</text>
              </button>
              <!-- #endif -->
              <!-- #ifndef MP-WEIXIN -->
              <uni-view class="share-group" :class="{ 'share-group-hover': isShareHover }" @click="sharePosition" @touchstart="handleTouchStart" @touchend="handleTouchEnd" @touchcancel="handleTouchEnd">
                <uni-view class="share-tooltip">
                  <uni-view class="share-tooltip-content">
                    <svg class="share-svg-stroke" xmlns="http://www.w3.org/2000/svg" width="20px" height="20px" viewBox="0 0 24 24" fill="none">
                      <circle cx="12" cy="12" r="9" stroke-linejoin="round"></circle>
                      <path d="M12 3C12 3 8.5 6 8.5 12C8.5 18 12 21 12 21" stroke-linejoin="round"></path>
                      <path d="M12 3C12 3 15.5 6 15.5 12C15.5 18 12 21 12 21" stroke-linejoin="round"></path>
                      <path d="M3 12H21" stroke-linejoin="round"></path>
                      <path d="M19.5 7.5H4.5" stroke-linejoin="round"></path>
                      <g>
                        <path d="M19.5 16.5H4.5" stroke-linejoin="round"></path>
                      </g>
                    </svg>
                    <uni-text>分享职位</uni-text>
                  </uni-view>
                  <uni-view class="share-tooltip-arrow"></uni-view>
                  <uni-view class="share-tooltip-overlay">
                    <uni-view class="share-tooltip-overlay-arrow"></uni-view>
                  </uni-view>
                </uni-view>
                <uni-view class="share-btn-main">
                  <svg class="share-svg-fill" xmlns="http://www.w3.org/2000/svg" width="20px" height="20px" viewBox="0 0 1024 1024">
                    <path d="M911.6 651.6l0 209.2c0 36-30.4 66.2-66.2 66.2l-699.6 1.2c-35.8 0-65-29.2-65-65.2l1.2-699.6c0-35.8 30.4-66.2 66.2-66.2l387 0L535.2 20.2 148.2 20.2c-81.8 0-143 82.8-143 156.8l0 686c0 77.6 63 140.8 140.8 140.8l686 0c82 0 156.6-68.2 156.6-143L988.6 651.6 911.6 651.6 911.6 651.6zM730.2 60.8l288.6 289.2L730.2 639l0-165.2c0 0-286.4-31.8-453.6 206.6 0 0 52.6-454.4 453.6-454.4L730.2 60.8 730.2 60.8z" fill="#2c2c2c"></path>
                  </svg>
                  <uni-text class="share-btn-text">分享职位</uni-text>
                </uni-view>
              </uni-view>
              <!-- #endif -->
            </view>
          </view>
        </view>
        <view class="meta-row">
          <text class="tag origin-provincial" v-if="originLabel && position?.position_origin === 0">{{ originLabel }}</text>
          <text class="tag origin-enterprise" v-if="originLabel && position?.position_origin === 1">{{ originLabel }}</text>
          <text class="tag origin-other" v-if="originLabel && position?.position_origin !== 0 && position?.position_origin !== 1">{{ originLabel }}</text>
          <text class="tag primary" v-if="position.position_type">{{ position.position_type }}</text>
          <text class="tag success" v-if="position.quota">{{ position.quota }}人</text>
          <text class="tag warning" v-if="position.year">{{ position.year }}年</text>
          <!-- <text class="tag status" v-if="currentStatusSimple" @click="showTimelineModal = true">{{ currentStatusSimple }}</text> -->
        </view>
      </view>

      <view class="card">
        <view class="card-title">基本信息</view>
        <view class="info-row" v-if="position.position_code">
          <text class="label">职位代码</text>
          <text class="value" selectable>{{ position.position_code }}</text>
        </view>
        <view class="info-row" v-if="position.region_dept">
          <text class="label">地区部门</text>
          <text class="value">{{ position.region_dept }}</text>
        </view>
        <view class="info-row" v-if="position.exam_region">
          <text class="label">考区</text>
          <text class="value">{{ position.exam_region }}</text>
        </view>
        <view class="info-row" v-if="position.recruit_unit">
          <text class="label">招录单位</text>
          <text class="value">{{ position.recruit_unit }}</text>
        </view>
        <view class="info-row" v-if="position.unit_level">
          <text class="label">单位层级</text>
          <text class="value">{{ position.unit_level }}</text>
        </view>
        <view class="info-row" v-if="position.position_nature">
          <text class="label">职位性质</text>
          <text class="value">{{ position.position_nature }}</text>
        </view>
        <view class="info-row" v-if="position.rank_level">
          <text class="label">职级层次</text>
          <text class="value">{{ position.rank_level }}</text>
        </view>
        <view class="info-row" v-if="phoneList.length > 0">
          <text class="label">咨询电话</text>
          <view class="value phone-list">
            <view 
              v-for="(phone, index) in phoneList" 
              :key="index" 
              class="phone-item link" 
              @click="makeCall(phone)"
            >
              {{ phone }}
            </view>
          </view>
        </view>
      </view>

      <view class="card">
        <view class="card-title">学历与专业</view>
        <view class="info-row" v-if="position.education">
          <text class="label">学历要求</text>
          <text class="value">{{ position.education }}</text>
        </view>
        <view class="info-row" v-if="position.degree">
          <text class="label">学位要求</text>
          <text class="value">{{ position.degree }}</text>
        </view>
        <view class="info-row" v-if="position.major">
          <text class="label">专业要求</text>
          <text class="value">{{ position.major }}</text>
        </view>
      </view>

      <view class="card">
        <view class="card-title">报考要求</view>
        
        <!-- 核心要求 Tag 展示区 -->
        <view class="tags-container">
            <view class="tag-item" v-if="position.grassroots_exp">
                <text class="tag-label">基层经历</text>
                <text class="tag-value">{{ position.grassroots_exp }}</text>
            </view>
            <view class="tag-item" v-if="position.political_status">
                <text class="tag-label">政治面貌</text>
                <text class="tag-value">{{ position.political_status }}</text>
            </view>
            <view class="tag-item" v-if="position.candidate_identity">
                <text class="tag-label">人员身份</text>
                <text class="tag-value">{{ position.candidate_identity }}</text>
            </view>
            <view class="tag-item" v-if="position.gender">
                <text class="tag-label">性别要求</text>
                <text class="tag-value">{{ position.gender }}</text>
            </view>
            <view class="tag-item" v-if="formattedMaxAge">
                <text class="tag-label">年龄要求</text>
                <text class="tag-value">{{ formattedMaxAge }}</text>
            </view>
            <view class="tag-item" v-if="position.domicile">
                <text class="tag-label">户籍要求</text>
                <text class="tag-value">{{ position.domicile }}</text>
            </view>
            <view class="tag-item" v-if="position.certification">
                <text class="tag-label">证书要求</text>
                <text class="tag-value">{{ position.certification }}</text>
            </view>
            <view class="tag-item" v-if="position.min_service_years">
                <text class="tag-label">服务年限</text>
                <text class="tag-value">{{ position.min_service_years }}</text>
            </view>
            <view class="tag-item" v-if="position.fresh_grad">
                <text class="tag-label">应届生</text>
                <text class="tag-value">{{ position.fresh_grad }}</text>
            </view>
        </view>

        <!-- 其他要求独立高亮展示 -->
        <view class="special-requirement-box" v-if="position.other_requirements">
             <view class="sr-title">
                 <text class="icon">⚠️</text>
                 <text>特别注意 / 其他要求</text>
             </view>
             <text class="sr-content">{{ position.other_requirements }}</text>
        </view>
      </view>

      <view class="card">
        <view class="card-title">考试信息</view>
        <view class="info-row" v-if="position.exam_ratio">
          <text class="label">开考比例</text>
          <text class="value">{{ position.exam_ratio }}</text>
        </view>
        <view class="info-row" v-if="position.exam_subjects">
          <text class="label">笔试科目</text>
          <text class="value">{{ position.exam_subjects }}</text>
        </view>
        <view class="info-row" v-if="position.exam_type">
          <text class="label">考试类型</text>
          <text class="value">{{ position.exam_type }}</text>
        </view>
        <view class="info-row" v-if="position.interview_ratio">
          <text class="label">面试比例</text>
          <text class="value">{{ position.interview_ratio }}</text>
        </view>
        <view class="info-row" v-if="position.inspection_ratio">
          <text class="label">考察比例</text>
          <text class="value">{{ position.inspection_ratio }}</text>
        </view>
        <view class="info-row" v-if="position.physical_test">
          <text class="label">体能测评</text>
          <text class="value">{{ position.physical_test }}</text>
        </view>
        <view class="info-row" v-if="position.physical_test_standards">
          <text class="label">体测标准</text>
          <text class="value">{{ position.physical_test_standards }}</text>
        </view>
        <view class="info-row" v-if="position.medical_test_standards">
          <text class="label">体检标准</text>
          <text class="value">{{ position.medical_test_standards }}</text>
        </view>
      </view>
      
      <view class="description-card" v-if="position.description">
         <view class="card-title">职位描述</view>
         <text class="desc-text">{{ position.description }}</text>
      </view>

    </view>
    <view v-else class="empty-container">
      <text>未找到职位信息</text>
    </view>
    
    <!-- 报考进度弹窗 -->
    <view class="modal-mask" v-if="showTimelineModal" @click="showTimelineModal = false">
        <view class="modal-content" @click.stop>
            <view class="modal-header">
                <text class="modal-title">报考进度时间轴</text>
                <text class="close-btn" @click="showTimelineModal = false">×</text>
            </view>
            <scroll-view scroll-y class="modal-body">
                 <view class="steps-container">
                  <view 
                    v-for="(step, index) in timelineSteps" 
                    :key="index" 
                    class="step-item"
                    :class="[step.status]"
                  >
                    <view class="step-icon">
                      <text v-if="step.status === 'finished'">✓</text>
                      <text v-else-if="step.status === 'process'" class="process-dot"></text>
                      <text v-else>{{ index + 1 }}</text>
                    </view>
                    <view class="step-content">
                      <text class="step-title">{{ step.title }}</text>
                      <text class="step-date">{{ step.date }}</text>
                    </view>
                    <view class="step-line" v-if="index < timelineSteps.length - 1"></view>
                  </view>
                </view>
            </scroll-view>
        </view>
    </view>
    
    <!-- 报错弹窗 -->
    <view class="report-modal-mask" v-if="showReportModal" @click="showReportModal = false">
        <view class="report-modal" @click.stop>
            <view class="modal-top">
                <view class="modal-icon">⚠️</view>
                <text class="modal-title">信息报错</text>
                <text class="modal-subtitle">感谢您的反馈，我们会尽快核实处理</text>
                <view class="modal-close" @click="showReportModal = false">✕</view>
            </view>
            
            <scroll-view scroll-y class="modal-scroll">
                <view class="section-title">请选择问题类型</view>
                
                <view class="type-grid">
                    <view 
                        class="type-card" 
                        :class="{ active: reportType === 'info_error' }"
                        @click="reportType = 'info_error'"
                    >
                        <view class="type-icon-wrap">
                            <text class="type-icon">📋</text>
                        </view>
                        <text class="type-name">信息有误</text>
                        <text class="type-desc">如招聘要求、人数等</text>
                    </view>
                    

                    
                    <view 
                        class="type-card" 
                        :class="{ active: reportType === 'missing' }"
                        @click="reportType = 'missing'"
                    >
                        <view class="type-icon-wrap">
                            <text class="type-icon">📭</text>
                        </view>
                        <text class="type-name">内容缺失</text>
                        <text class="type-desc">关键信息为空</text>
                    </view>
                    
                    <view 
                        class="type-card" 
                        :class="{ active: reportType === 'other' }"
                        @click="reportType = 'other'"
                    >
                        <view class="type-icon-wrap">
                            <text class="type-icon">💭</text>
                        </view>
                        <text class="type-name">其他问题</text>
                        <text class="type-desc">其他错误类型</text>
                    </view>
                </view>
                
                <view class="desc-section">
                    <view class="desc-header">
                    <text class="desc-label">补充说明（必填）</text>
                    <text class="desc-limit">{{ reportDesc.length }}/200</text>
                </view>
                    <view class="textarea-wrap">
                        <textarea 
                            class="desc-input" 
                            v-model="reportDesc" 
                            placeholder="请尽可能详细描述问题，以便我们更快核实..."
                            maxlength="200"
                            :show-confirm-bar="false"
                            cursor-spacing="120"
                        ></textarea>
                    </view>
                </view>
            </scroll-view>
            
            <view class="modal-footer">
                <button 
                    class="btn-submit" 
                    :class="{ disabled: !reportType }"
                    :disabled="!reportType || submitting" 
                    @click="submitReport"
                >
                    <text v-if="submitting">提交中...</text>
                    <text v-else-if="!reportType">请先选择问题类型</text>
                    <text v-else>提交反馈</text>
                </button>
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
      position: null,
      timeline: null,
      showTimelineModal: false,
      isLoading: true,
      errorMsg: '',
      currentId: '',
      showReportModal: false,
      reportType: '',
      reportDesc: '',
      submitting: false,
      canReport: true,
      isShareHover: false
    }
  },
  onLoad(options) {
    // 开启反馈限制
    const today = new Date().toISOString().split('T')[0];
    const lastReportDate = uni.getStorageSync('lastReportDate');
    
    if (lastReportDate === today) {
      this.canReport = false;
    }
    
    if (options.id) {
      this.currentId = options.id;
      this.loadData(options.id);
    } else {
      this.isLoading = false;
      this.errorMsg = '参数错误：未提供职位ID';
    }
  },
  computed: {
    /**
     * 计算岗位来源标签文本
     * 0=省考，1=事业，其它=其他；无值返回空
     */
    originLabel() {
      const v = this.position?.position_origin;
      if (v === 0) return '省考';
      if (v === 1) return '事业编';
      if (v === undefined || v === null) return '';
      return '其他';
    },
    timelineSteps() {
      if (!this.timeline) return [];
      
      const steps = [];
      const now = new Date();
      const today = now.toISOString().split('T')[0];
      
      const addStep = (title, dateKey, endDateKey = null) => {
        if (!this.timeline[dateKey]) return;
        
        let dateStr = this.timeline[dateKey];
        let status = 'wait';
        let fullDateStr = dateStr;
        
        if (endDateKey && this.timeline[endDateKey]) {
            fullDateStr = `${dateStr} 至 ${this.timeline[endDateKey]}`;
            if (today > this.timeline[endDateKey]) {
                status = 'finished';
            } else if (today >= dateStr) {
                status = 'process';
            }
        } else {
            if (today > dateStr) {
                status = 'finished';
            } else if (today === dateStr) {
                status = 'process';
            }
        }
        
        steps.push({
            title,
            date: fullDateStr,
            status,
            rawDate: dateStr
        });
      };
      
      addStep('报名', 'signup_start', 'signup_end');
      addStep('缴费', 'signup_end', 'payment_end'); // 简化：缴费通常在报名后
      addStep('打印准考证', 'admit_card_start');
      addStep('笔试', 'exam_date');
      addStep('查分', 'score_date');
      addStep('面试', 'interview_date_start');
      
      return steps;
    },
    currentStatusSimple() {
        if (!this.timelineSteps || this.timelineSteps.length === 0) return '';
        
        const activeStep = this.timelineSteps.find(s => s.status === 'process');
        if (activeStep) {
            return `${activeStep.title}中 >`;
        }
        
        const nextStep = this.timelineSteps.find(s => s.status === 'wait');
        if (nextStep) {
            let date = nextStep.rawDate;
            if (date && date.includes('-')) {
                // 提取 MM-DD
                date = date.substring(5);
            }
            return `待${nextStep.title} ${date} >`;
        }
        
        return '已结束 >';
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
      if (!this.position || !this.position.max_age) return '';
      const age = String(this.position.max_age).trim();
      
      // 已经包含限定词或范围，直接返回
        if (age.includes('以下') || age.includes('以内') || age.includes('最大') || age.includes('不超过') || age.includes('以上') || age.includes('-') || age.includes('至') || age.includes('≤')) {
          return age;
        }
       
       // 提取数字
       const match = age.match(/(\d+)/);
       if (match) {
         return `≤${match[1]}周岁`;
       }
      
      return age;
    }
  },
  // 微信小程序分享配置
  onShareAppMessage() {
    const title = this.position?.position_name || '职位详情';
    const id = this.currentId || this.position?.id;
    return {
      title: title,
      path: `/pages/detail/detail?id=${id}`,
      imageUrl: '/static/icons/share.png'
    };
  },
  onShareTimeline() {
    const title = this.position?.position_name || '职位详情';
    const id = this.currentId || this.position?.id;
    return {
      title: title,
      path: `/pages/detail/detail?id=${id}`,
      imageUrl: '/static/icons/share.png'
    };
  },
  methods: {
    /**
     * 根据ID加载职位详情
     * @param {String} id 职位ID
     */
    async loadData(id) {
      this.isLoading = true;
      this.errorMsg = '';
      try {
        console.log('正在加载职位详情，ID:', id);
        this.position = await positionService.getPositionById(id);
        console.log('职位详情加载成功:', this.position);
        
        if (this.position) {
            // 加载时间线
            if (this.position.province_code && this.position.year) {
                const category = this.position.position_origin === 1 ? 1 : 0;
                this.timeline = await positionService.getExamTimeline(this.position.province_code, this.position.year, category);
            }
        } else {
            this.errorMsg = '未找到该职位信息';
        }
      } catch (e) {
        console.error('加载职位详情失败:', e);
        this.errorMsg = '加载失败，请检查网络或稍后重试';
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
     * 触摸开始事件处理
     */
    handleTouchStart() {
      this.isShareHover = true;
    },
    /**
     * 触摸结束事件处理
     */
    handleTouchEnd() {
      this.isShareHover = false;
    },
    /**
     * 拨打咨询电话
     */
    makeCall(phoneNumber) {
      if (phoneNumber) {
        uni.makePhoneCall({
          phoneNumber: phoneNumber
        });
      }
    }
    ,
    /**
     * 触发分享逻辑（非微信小程序平台）
     * - H5：优先使用 Web Share API，回退为复制链接
     * - App：可根据需要扩展为 uni.share
     */
    async sharePosition() {
      try {
        const title = this.position?.position_name || '职位详情';
        const id = this.currentId || this.position?.id;
        const origin = typeof location !== 'undefined' ? location.origin : '';
        const url = `${origin}/#/pages/detail/detail?id=${id}`;

        if (typeof navigator !== 'undefined' && navigator.share) {
          await navigator.share({
            title,
            text: `查看职位：${title}`,
            url
          });
          uni.showToast({ title: '已分享', icon: 'success' });
          return;
        }

        await this.copyToClipboard(url);
        uni.showToast({ title: '链接已复制', icon: 'success' });
      } catch (e) {
        console.error('分享失败', e);
        uni.showToast({ title: '分享失败', icon: 'none' });
      }
    },
    /**
     * 复制文本到剪贴板（H5 回退方案）
     * @param {String} text 需要复制的文本
     */
    async copyToClipboard(text) {
      if (typeof navigator !== 'undefined' && navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(text);
        return;
      }
      if (typeof document !== 'undefined') {
        const input = document.createElement('input');
        input.value = text;
        document.body.appendChild(input);
        input.select();
        try {
          document.execCommand('copy');
        } finally {
          document.body.removeChild(input);
        }
      }
    },
    async submitReport() {
    if (!this.reportType) {
      uni.showToast({ title: '请先选择问题类型', icon: 'none', duration: 2000 });
      return;
    }
    
    if (!this.reportDesc || this.reportDesc.trim() === '') {
      uni.showToast({ title: '请填写补充说明', icon: 'none', duration: 2000 });
      return;
    }
    
    // 开启反馈限制
    const today = new Date().toISOString().split('T')[0];
    const lastReportDate = uni.getStorageSync('lastReportDate');
    
    if (lastReportDate === today) {
      uni.showToast({ title: '您今天已经提交过反馈，请明天再试', icon: 'none', duration: 2000 });
      return;
    }
      
      this.submitting = true;
      
      try {
        const reportData = {
          position_id: this.currentId,
          position_name: this.position?.position_name,
          report_type: this.reportType,
          description: this.reportDesc
        };
        
        console.log('提交报错反馈:', reportData);
        
        // 调用 API 提交反馈
        await positionService.submitReport(reportData);
        
        // 开启反馈限制
        // 保存今天的日期到本地存储
        const today = new Date().toISOString().split('T')[0];
        uni.setStorageSync('lastReportDate', today);
        
        // 更新 canReport 状态
        this.canReport = false;
        
        // 关闭弹窗并重置表单
        this.showReportModal = false;
        this.reportType = '';
        this.reportDesc = '';
        
        uni.showModal({
          title: '提交成功',
          content: '感谢您的反馈，我们会尽快核实处理！',
          showCancel: false,
          confirmText: '知道了',
          confirmColor: '#1890ff',
          success: function (res) {}
        });
      } catch (e) {
        console.error('提交反馈失败:', e);
        uni.showToast({ title: '提交失败，请稍后重试', icon: 'none', duration: 2000 });
      } finally {
        this.submitting = false;
      }
    }
  }
  ,
  // #ifdef MP-WEIXIN
  /**
   * 微信小程序分享消息配置
   * 控制分享标题、路径与（可选）图片
   */
  onShareAppMessage() {
    const title = this.position?.position_name || '职位详情';
    const id = this.currentId || this.position?.id;
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
    const title = this.position?.position_name || '职位详情';
    const id = this.currentId || this.position?.id;
    return {
      title: `助残公考｜${title}`,
      query: `id=${id}`
    };
  }
  // #endif
}
</script>

<style lang="scss" scoped>
.container {
  padding: 20rpx;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.header-section {
  padding: 30rpx;
  background: #fff;
  border-radius: 16rpx;
  margin-bottom: 20rpx;
  
  .title-row {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 20rpx;
    
    .title {
      font-size: 40rpx;
      font-weight: bold;
      color: #333;
      flex: 1;
      margin-right: 20rpx;
      line-height: 1.4;
    }
    
    .action-area {
      flex-shrink: 0;
      margin-top: 6rpx;
      display: flex;
      align-items: center;
      gap: 16rpx;
    }
    
    .report-btn {
      display: flex;
      align-items: center;
      padding: 0 20rpx;
      height: 48rpx;
      background: #fff1f0;
      border-radius: 24rpx;
      border: 1rpx solid #ffa39e;
      
      .report-icon {
        width: 24rpx;
        height: 24rpx;
        margin-right: 6rpx;
        vertical-align: middle;
      }
      
      .report-text {
        font-size: 24rpx;
        color: #f5222d;
      }
      
      &.disabled {
        background: #f5f5f5;
        border: 1rpx solid #d9d9d9;
        
        .report-icon {
          opacity: 0.5;
        }
        
        .report-text {
          color: #bfbfbf;
        }
      }
    }
    
    .share-area {
      flex-shrink: 0;
    }
  }
  
  .meta-row {
    display: flex;
    gap: 16rpx;
    
    .tag {
      padding: 6rpx 16rpx;
      border-radius: 8rpx;
      font-size: 24rpx;
      
      &.primary { background: #e6f7ff; color: #1890ff; }
      &.success { background: #f6ffed; color: #52c41a; }
      &.warning { background: #fff7e6; color: #fa8c16; }
      &.status { background: #f9f0ff; color: #722ed1; font-weight: 500; }
      &.origin-provincial { background: #e6f7ff; color: #096dd9; border: 1rpx solid #91d5ff; }
      &.origin-enterprise { background: #fff7e6; color: #d46b08; border: 1rpx solid #ffd591; }
      &.origin-other { background: #fafafa; color: #595959; border: 1rpx solid #d9d9d9; }
    }
  }
}

.card {
  background: #fff;
  border-radius: 16rpx;
  padding: 30rpx;
  margin-bottom: 20rpx;
  
  .card-title {
    font-size: 30rpx;
    font-weight: bold;
    color: #333;
    margin-bottom: 24rpx;
    padding-left: 16rpx;
    border-left: 6rpx solid #1890ff;
  }
  
  .tags-container {
      display: flex;
      flex-wrap: wrap;
      gap: 16rpx;
      margin-bottom: 24rpx;
      
      .tag-item {
          background: #f5f7fa;
          border-radius: 8rpx;
          padding: 8rpx 16rpx;
          display: flex;
          align-items: center;
          gap: 8rpx;
          
          .tag-label {
              font-size: 24rpx;
              color: #999;
          }
          
          .tag-value {
              font-size: 26rpx;
              color: #333;
              font-weight: 500;
          }
      }
  }
  
  .special-requirement-box {
      background: #fffbe6;
      border: 1px solid #ffe58f;
      border-radius: 12rpx;
      padding: 20rpx;
      margin-top: 10rpx;
      
      .sr-title {
          display: flex;
          align-items: center;
          gap: 8rpx;
          margin-bottom: 12rpx;
          font-size: 26rpx;
          font-weight: bold;
          color: #fa8c16;
          
          .icon { font-size: 28rpx; }
      }
      
      .sr-content {
          font-size: 28rpx;
          color: #333;
          line-height: 1.6;
      }
  }
  
  .info-row {
    display: flex;
    justify-content: space-between;
    margin-bottom: 20rpx;
    line-height: 1.5;
    
    &:last-child {
      margin-bottom: 0;
    }
    
    .label {
      width: 160rpx;
      color: #999;
      font-size: 28rpx;
      flex-shrink: 0;
    }
    
    .value {
      flex: 1;
      color: #333;
      font-size: 28rpx;
      
      &.link {
        color: #1890ff;
        text-decoration: underline;
      }
      
      &.highlight {
        color: #ff4d4f;
      }
    }
    
    .phone-list {
      display: flex;
      flex-direction: column;
      
      .phone-item {
        margin-bottom: 8rpx;
        &:last-child {
          margin-bottom: 0;
        }
      }
    }
  }
}

.share-btn {
  font-size: 24rpx !important;
  color: #666 !important;
  background: #f5f7fa !important;
  padding: 0 24rpx !important;
  height: 48rpx !important;
  line-height: 48rpx !important;
  border-radius: 24rpx !important;
  border: 1px solid #eee !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 8rpx !important;
  min-width: 120rpx !important;
  
  &::after {
    border: none !important;
  }
  
  &:active {
    background: #e6e6e6 !important;
  }
}

.share-icon {
  width: 28rpx;
  height: 28rpx;
  vertical-align: middle;
}

.share-btn svg {
  width: 20px;
  height: 20px;
  vertical-align: middle;
}

.share-label {
  font-size: 24rpx;
  color: #666;
  vertical-align: middle;
}

/* New share button styles */
.share-group {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  color: #525252;
  font-size: 14rpx;
  font-weight: bold;
}

.share-tooltip {
  position: absolute;
  opacity: 0;
  transform: translateY(-300%) skewY(20deg);
  transition: all 500ms ease;
  transform-origin: center;
  pointer-events: none;
}

.share-group-hover .share-tooltip {
  opacity: 1;
  transform: translateY(-150%) skewY(0);
  transition-delay: 500ms;
}

.share-tooltip-content {
  background-color: #dcfce7;
  display: flex;
  align-items: center;
  gap: 4rpx;
  padding: 8rpx;
  border-radius: 8rpx;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.share-svg-stroke {
  stroke: #525252;
}

.share-svg-fill {
  fill: #525252;
  width: 20px;
  height: 20px;
}

.share-tooltip-arrow {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  background-color: #dcfce7;
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(100%) translateY(50%) rotate(45deg);
  padding: 4rpx;
}

.share-tooltip-overlay {
  border-radius: 8rpx;
  background-color: #ffffff;
  opacity: 1;
  transform: scale(1);
  width: 100%;
  height: 100%;
  position: absolute;
  top: 0;
  left: 0;
  transition: all 500ms ease;
  transition-delay: 0;
  pointer-events: none;
}

.share-group-hover .share-tooltip-overlay {
  opacity: 0;
  transform: scale(1.15);
  transition-delay: 700ms;
}

.share-tooltip-overlay-arrow {
  border-bottom: 1rpx solid #ffffff;
  border-right: 1rpx solid #ffffff;
  background-color: #ffffff;
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(100%) translateY(50%) rotate(45deg);
  padding: 4rpx;
}

.share-btn-main {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  display: flex;
  align-items: center;
  gap: 4rpx;
  background: linear-gradient(135deg, #dcfce7, #fef9c3);
  padding: 12rpx;
  border-radius: 9999rpx;
  cursor: pointer;
  transition: all 300ms ease;
  -webkit-tap-highlight-color: transparent;
}

.share-group-hover .share-btn-main {
  gap: 8rpx;
}

.share-btn-text {
  font-size: 0;
  transition: font-size 300ms ease;
}

.share-group-hover .share-btn-text {
  font-size: 14rpx;
}

.step-item {
      display: flex;
      position: relative;
      padding-bottom: 40rpx;
      
      &:last-child {
          padding-bottom: 0;
          .step-line { display: none; }
      }
      
      .step-icon {
          width: 40rpx;
          height: 40rpx;
          border-radius: 50%;
          background: #e0e0e0;
          color: #fff;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 24rpx;
          z-index: 1;
          margin-right: 20rpx;
          flex-shrink: 0;
          
          .process-dot {
              width: 16rpx;
              height: 16rpx;
              background: #fff;
              border-radius: 50%;
          }
      }
      
      .step-line {
          position: absolute;
          left: 19rpx;
          top: 40rpx;
          bottom: 0;
          width: 2rpx;
          background: #e0e0e0;
      }
      
      .step-content {
          flex: 1;
          
          .step-title {
              font-size: 28rpx;
              color: #666;
              font-weight: 500;
              margin-bottom: 4rpx;
              display: block;
          }
          
          .step-date {
              font-size: 24rpx;
              color: #999;
          }
      }
      
      // 状态样式
      &.finished {
          .step-icon {
              background: #52c41a;
          }
          .step-line {
              background: #52c41a;
          }
          .step-title {
              color: #333;
          }
      }
      
      &.process {
          .step-icon {
              background: #1890ff;
              box-shadow: 0 0 0 6rpx rgba(24, 144, 255, 0.2);
          }
          .step-title {
              color: #1890ff;
              font-weight: bold;
          }
      }
  }
  
  .current-status-text {
      margin-top: 30rpx;
      padding-top: 20rpx;
      border-top: 1px dashed #eee;
      display: flex;
      align-items: center;
      gap: 12rpx;
      color: #1890ff;
      font-size: 28rpx;
      font-weight: 500;
  }

.description-card {
  @extend .card;
  .desc-text {
    font-size: 28rpx;
    color: #555;
    line-height: 1.8;
  }
}

.loading, .state-container, .empty-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding-top: 100rpx;
  color: #999;
}

.state-text {
  margin-bottom: 20rpx;
  font-size: 28rpx;
  color: #666;
}

.retry-btn {
  margin-top: 20rpx;
}

.modal-mask {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 999;
    display: flex;
    align-items: center;
    justify-content: center;
}

.modal-content {
    width: 80%;
    max-height: 80vh;
    background: #fff;
    border-radius: 20rpx;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    animation: modal-pop 0.3s ease-out;
    
    .modal-header {
        padding: 30rpx;
        border-bottom: 1px solid #eee;
        display: flex;
        justify-content: space-between;
        align-items: center;
        
        .modal-title {
            font-size: 32rpx;
            font-weight: bold;
            color: #333;
        }
        
        .close-btn {
            font-size: 40rpx;
            color: #999;
            padding: 0 10rpx;
        }
    }
    
    .modal-body {
        padding: 30rpx;
        max-height: 60vh; // 确保滚动
        
        /* 复用之前的 timeline 样式 */
        .steps-container {
            display: flex;
            flex-direction: column;
            gap: 0;
            padding-left: 20rpx;
        }
        
        .step-item {
            display: flex;
            position: relative;
            padding-bottom: 40rpx;
            
            &:last-child {
                padding-bottom: 0;
                .step-line { display: none; }
            }
            
            .step-icon {
                width: 40rpx;
                height: 40rpx;
                border-radius: 50%;
                background: #e0e0e0;
                color: #fff;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24rpx;
                z-index: 1;
                margin-right: 20rpx;
                flex-shrink: 0;
                
                .process-dot {
                    width: 16rpx;
                    height: 16rpx;
                    background: #fff;
                    border-radius: 50%;
                }
            }
            
            .step-line {
                position: absolute;
                left: 19rpx;
                top: 40rpx;
                bottom: 0;
                width: 2rpx;
                background: #e0e0e0;
            }
            
            .step-content {
                flex: 1;
                
                .step-title {
                    font-size: 28rpx;
                    color: #666;
                    font-weight: 500;
                    margin-bottom: 4rpx;
                    display: block;
                }
                
                .step-date {
                    font-size: 24rpx;
                    color: #999;
                }
            }
            
            // 状态样式
            &.finished {
                .step-icon {
                    background: #52c41a;
                }
                .step-line {
                    background: #52c41a;
                }
                .step-title {
                    color: #333;
                }
            }
            
            &.process {
                .step-icon {
                    background: #1890ff;
                    box-shadow: 0 0 0 6rpx rgba(24, 144, 255, 0.2);
                }
                .step-title {
                    color: #1890ff;
                    font-weight: bold;
                }
            }
        }
    }
}

.report-modal-mask {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.65);
    backdrop-filter: blur(10rpx);
    z-index: 9999;
    display: flex;
    align-items: flex-end;
    justify-content: center;
    animation: fadeIn 0.2s ease-out;
}

.report-modal {
    width: 100%;
    max-height: 88vh;
    background: #fff;
    border-radius: 36rpx 36rpx 0 0;
    animation: slideUp 0.25s cubic-bezier(0.25, 0.8, 0.25, 1);
    
    .modal-top {
        position: relative;
        padding: 40rpx 36rpx 32rpx;
        background: linear-gradient(135deg, #ff4d4f 0%, #ff6b4a 100%);
        border-radius: 36rpx 36rpx 0 0;
        text-align: center;
        
        .modal-icon {
            width: 88rpx;
            height: 88rpx;
            background: rgba(255, 255, 255, 0.25);
            border-radius: 50%;
            font-size: 44rpx;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 16rpx;
        }
        
        .modal-title {
            font-size: 38rpx;
            font-weight: 700;
            color: #fff;
            display: block;
            margin-bottom: 8rpx;
        }
        
        .modal-subtitle {
            font-size: 24rpx;
            color: rgba(255, 255, 255, 0.85);
            display: block;
            line-height: 1.4;
        }
        
        .modal-close {
            position: absolute;
            top: 24rpx;
            right: 24rpx;
            width: 56rpx;
            height: 56rpx;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 50%;
            font-size: 32rpx;
            color: #fff;
            display: flex;
            align-items: center;
            justify-content: center;
            
            &:active {
                transform: scale(0.92);
                background: rgba(255, 255, 255, 0.3);
            }
        }
    }
    
    .modal-scroll {
        padding: 32rpx;
        max-height: 55vh;
        overflow-y: auto;
        box-sizing: border-box;
    }
    
    .section-title {
        font-size: 30rpx;
        font-weight: 600;
        color: #333;
        margin-bottom: 28rpx;
        text-align: center;
    }
    
    .type-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 24rpx;
        margin-bottom: 32rpx;
        justify-content: space-between;
        
        .type-card {
            width: calc(33.33% - 16rpx);
            background: #f7f8fa;
            border-radius: 20rpx;
            padding: 32rpx 20rpx;
            text-align: center;
            border: 2rpx solid transparent;
            transition: all 0.3s ease;
            box-sizing: border-box;
            box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.05);
            
            &:active {
                transform: scale(0.95);
                background: #f0f1f4;
                box-shadow: 0 1rpx 4rpx rgba(0, 0, 0, 0.1);
            }
            
            &.active {
                background: #e6f7ff;
                border-color: #1890ff;
                box-shadow: 0 4rpx 12rpx rgba(24, 144, 255, 0.2);
                
                .type-icon-wrap {
                    background: #1890ff;
                    box-shadow: 0 2rpx 8rpx rgba(24, 144, 255, 0.3);
                }
            }
            
            .type-icon-wrap {
                width: 72rpx;
                height: 72rpx;
                background: #e8e8e8;
                border-radius: 16rpx;
                font-size: 36rpx;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                margin-bottom: 16rpx;
                transition: all 0.3s ease;
            }
            
            .type-name {
                font-size: 28rpx;
                font-weight: 600;
                color: #333;
                display: block;
                margin-bottom: 8rpx;
                line-height: 1.3;
            }
            
            .type-desc {
                font-size: 22rpx;
                color: #999;
                display: block;
                line-height: 1.4;
            }
        }
    }
    
    .desc-section {
        .desc-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12rpx;
            
            .desc-label {
                font-size: 26rpx;
                font-weight: 600;
                color: #333;
            }
            
            .desc-limit {
                font-size: 22rpx;
                color: #999;
            }
        }
        
        .textarea-wrap {
            .desc-input {
                width: 100%;
                height: 180rpx;
                padding: 20rpx;
                background: #f7f8fa;
                border: 2rpx solid #e8e8e8;
                border-radius: 16rpx;
                font-size: 28rpx;
                color: #333;
                line-height: 1.5;
                box-sizing: border-box;
                
                &:focus {
                    border-color: #1890ff;
                    background: #fff;
                }
            }
        }
    }
    
    .modal-footer {
        padding: 20rpx 32rpx 40rpx;
        background: #fff;
        
        .btn-submit {
            width: 100%;
            height: 88rpx;
            border-radius: 44rpx;
            font-size: 30rpx;
            font-weight: 600;
            display: flex;
            align-items: center;
            justify-content: center;
            border: none;
            background: linear-gradient(135deg, #ff4d4f 0%, #ff6b4a 100%);
            color: #fff;
            
            &[disabled] {
                background: linear-gradient(135deg, #ffb8b9 0%, #ffc4c5 100%);
                color: #fff;
                opacity: 0.6;
            }
            
            &.disabled {
                background: linear-gradient(135deg, #ffb8b9 0%, #ffc4c5 100%);
                color: #fff;
                opacity: 0.6;
            }
        }
    }
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

@keyframes slideUp {
    from { 
        opacity: 0;
        transform: translateY(100%);
    }
    to { 
        opacity: 1;
        transform: translateY(0);
    }
}
</style>
