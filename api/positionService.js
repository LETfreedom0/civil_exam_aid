import { callApi } from '../common/cloud'
import provinces from '../common/provinces.json'

// 缓存配置
const CACHE_CONFIG = {
  // 缓存过期时间（毫秒）
  POSITIONS_EXPIRY: 30 * 60 * 1000, // 30分钟
  TIMELINE_EXPIRY: 60 * 60 * 1000, // 1小时
  STATUS_EXPIRY: 60 * 60 * 1000, // 1小时
};

// 缓存存储
const cache = {
  positions: {
    data: null,
    timestamp: 0,
    params: null
  },
  timelines: new Map(), // 使用Map存储不同省份、年份、类别的时间线
  statuses: new Map(), // 使用Map存储不同省份、年份、类别的状态
  pendingRequests: new Map() // 存储正在进行的请求，避免重复请求
};

export const positionService = {
  // 获取职位列表（经 gwy-api 云函数查询 Supabase）
  async getPositions(params = {}) {
    // 检查缓存是否有效
    const now = Date.now();
    const cacheKey = JSON.stringify(params);

    if (cache.positions.data &&
        cache.positions.timestamp + CACHE_CONFIG.POSITIONS_EXPIRY > now &&
        JSON.stringify(cache.positions.params) === cacheKey) {
      console.log('使用缓存的职位数据');
      return cache.positions.data;
    }

    console.log('从云函数获取职位数据');

    // 与原逻辑一致：有省代码按省查，否则按市查
    const payload = {};
    if (params.provinceCode) {
      payload.provinceCode = params.provinceCode;
    } else if (params.city) {
      payload.city = params.city;
    }
    if (params.year) payload.year = params.year;

    let result = await callApi('getPositions', payload);

    // keyword / examType 过滤在服务端同样会做一遍，这里保留本地过滤兜底
    if (params.keyword) {
      const k = String(params.keyword).toLowerCase()
      result = result.filter(p => {
        const name = (p.position_name || '').toLowerCase()
        const unit = (p.recruit_unit || '').toLowerCase()
        const desc = (p.description || '').toLowerCase()
        const major = (p.major || '').toLowerCase()
        return name.includes(k) || unit.includes(k) || desc.includes(k) || major.includes(k)
      })
    }
    if (params.examType) {
      if (params.examType === '省考') {
        result = result.filter(p => p.position_origin === 0)
      } else if (params.examType === '事业编') {
        result = result.filter(p => p.position_origin === 1)
      }
    }

    // 更新缓存
    cache.positions = {
      data: result,
      timestamp: now,
      params: params
    };

    return result
  },

  // 获取所有可选城市
  async getCities() {
    return this.getProvinces();
  },

  // 获取所有可选省份/城市
  async getProvinces() {
    return provinces
  },

  // 获取职位详情
  async getPositionById(id) {
    if (!id || id === 'undefined' || id === 'null') {
        throw new Error('Invalid position ID');
    }
    return await callApi('getPositionById', { id })
  },

  // 获取考试时间线
  async getExamTimeline(provinceCode, year, category = 0) {
    // 检查缓存是否有效
    const cacheKey = `${provinceCode}_${year}_${category}`;
    const cachedData = cache.timelines.get(cacheKey);
    const now = Date.now();

    if (cachedData && cachedData.timestamp + CACHE_CONFIG.TIMELINE_EXPIRY > now) {
      console.log('使用缓存的时间线数据');
      return cachedData.data;
    }

    // 检查是否有正在进行的相同请求
    if (cache.pendingRequests.has(cacheKey)) {
      console.log('等待正在进行的时间线请求');
      return cache.pendingRequests.get(cacheKey);
    }

    console.log('从云函数获取时间线数据');

    // 创建请求Promise并缓存
    const requestPromise = (async () => {
      try {
        let data = null
        try {
          data = await callApi('getExamTimeline', {
            provinceCode,
            year,
            category,
          })
        } catch (e) {
          data = null
        }

        if (!data) {
          console.warn('未找到时间线数据，使用模拟数据')
          // 返回模拟数据
          const mockData = {
            signup_start: '2026-01-22',
            signup_end: '2026-01-26',
            payment_end: '2026-01-28',
            admit_card_start: '2026-02-20',
            exam_date: '2026-02-25',
            score_date: '2026-03-20',
            interview_date_start: '2026-04-15'
          };

          // 缓存模拟数据
          cache.timelines.set(cacheKey, {
            data: mockData,
            timestamp: now
          });

          return mockData;
        }

        // 缓存真实数据
        cache.timelines.set(cacheKey, {
          data: data,
          timestamp: now
        });

        return data
      } catch (e) {
        console.error('获取时间线失败', e)
        return null
      } finally {
        // 移除 pending request
        cache.pendingRequests.delete(cacheKey);
      }
    })();

    // 存储正在进行的请求
    cache.pendingRequests.set(cacheKey, requestPromise);

    return requestPromise;
  },

  // 获取数据更新统计信息
  async getUpdateStats() {
    const stats = await callApi('getStats')
    return {
      lastUpdateTime: stats.lastUpdate || '',
      newPositionsCount: 0,
      totalPositionsCount: stats.total || 0,
      updatedProvinces: stats.groups || []
    }
  },

  // 获取更新日志列表
  async getUpdateLogs() {
    return []
  },

  // 提交报错反馈
  async submitReport(reportData) {
    console.log('调用 submitReport 方法:', reportData);
    return await callApi('submitReport', {
      position_id: String(reportData.position_id || ''),
      position_name: String(reportData.position_name || ''),
      report_type: String(reportData.report_type || 'other'),
      description: String(reportData.description || ''),
      user_ip: reportData.user_ip || '',
    })
  },

  // 获取职位状态
  async getPositionStatus(provinceCode, year, category = 0) {
    // 检查缓存是否有效
    const cacheKey = `${provinceCode}_${year}_${category}`;
    const cachedData = cache.statuses.get(cacheKey);
    const now = Date.now();

    if (cachedData && cachedData.timestamp + CACHE_CONFIG.STATUS_EXPIRY > now) {
      console.log('使用缓存的职位状态数据');
      return cachedData.data;
    }

    // 检查是否有正在进行的相同请求
    if (cache.pendingRequests.has(cacheKey)) {
      console.log('等待正在进行的状态请求');
      return cache.pendingRequests.get(cacheKey);
    }

    console.log('从云函数获取职位状态数据');

    // 创建请求Promise并缓存
    const requestPromise = (async () => {
      try {
        let data = null
        try {
          data = await callApi('getExamTimeline', {
            provinceCode,
            year,
            category,
          })
        } catch (e) {
          data = null
        }

        let statusResult;

        if (!data || (!data.signup_start && data.status === 'unknown')) {
          console.warn('未找到时间线数据，使用年份判断')
          // 使用年份和月份判断
          const now = new Date();
          const currentYear = now.getFullYear();
          const currentMonth = now.getMonth() + 1; // 0-11 转换为 1-12

          if (year > currentYear) statusResult = { status: 'upcoming', label: '待开始' };
          else if (year === currentYear) {
            // 当前年份：如果当前月份大于6月，认为报名已结束
            if (currentMonth > 6) {
              statusResult = { status: 'finished', label: '已结束' };
            } else {
              statusResult = { status: 'running', label: '报名中' };
            }
          }
          else statusResult = { status: 'finished', label: '已结束' };
        } else {
          // 根据时间线判断状态
          const now = new Date();
          const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());

          // 转换日期字符串为Date对象
          const signupStart = data.signup_start ? new Date(data.signup_start) : null;
          const signupEnd = data.signup_end ? new Date(data.signup_end) : null;
          const examDate = data.exam_date ? new Date(data.exam_date) : null;
          const examEndDate = data.exam_end_date ? new Date(data.exam_end_date) : null;

          if (!signupStart) {
            // 没有报名开始时间，使用年份判断
            const currentYear = new Date().getFullYear();
            if (year > currentYear) statusResult = { status: 'upcoming', label: '待开始' };
            else if (year === currentYear) statusResult = { status: 'running', label: '报名中' };
            else statusResult = { status: 'finished', label: '已结束' };
          } else {
            if (today < signupStart) {
              statusResult = { status: 'upcoming', label: '待报名' };
            } else if (signupEnd && today <= signupEnd) {
              statusResult = { status: 'running', label: '报名中' };
            } else if (examDate && today < examDate) {
              statusResult = { status: 'pending', label: '待考试' };
            } else if (examEndDate && today <= examEndDate) {
              statusResult = { status: 'examined', label: '考试中' };
            } else {
              statusResult = { status: 'finished', label: '已结束' };
            }
          }
        }

        // 缓存状态结果
        cache.statuses.set(cacheKey, {
          data: statusResult,
          timestamp: now
        });

        return statusResult;
      } catch (e) {
        console.error('获取职位状态失败', e);
        // 出错时使用年份和月份判断
        const now = new Date();
        const currentYear = now.getFullYear();
        const currentMonth = now.getMonth() + 1; // 0-11 转换为 1-12

        let statusResult;
        if (year > currentYear) statusResult = { status: 'upcoming', label: '待开始' };
        else if (year === currentYear) {
          // 当前年份：如果当前月份大于6月，认为报名已结束
          if (currentMonth > 6) {
            statusResult = { status: 'finished', label: '已结束' };
          } else {
            statusResult = { status: 'running', label: '报名中' };
          }
        }
        else statusResult = { status: 'finished', label: '已结束' };

        // 缓存错误时的状态结果
        cache.statuses.set(cacheKey, {
          data: statusResult,
          timestamp: now
        });

        return statusResult;
      } finally {
        // 移除 pending request
        cache.pendingRequests.delete(cacheKey);
      }
    })();

    // 存储正在进行的请求
    cache.pendingRequests.set(cacheKey, requestPromise);

    return requestPromise;
  }
}
