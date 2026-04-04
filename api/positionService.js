import { supabase } from '../common/supabase'
import provinces from '../common/provinces.json'

export const positionService = {
  // 获取职位列表
  async getPositions(params = {}) {
    let query = supabase
      .from('positions')
      .select('*')
    
    if (params.provinceCode) {
      query = query.eq('province_code', params.provinceCode)
    } else if (params.city) {
      query = query.eq('city', params.city)
    }
    if (params.year) {
      query = query.eq('year', params.year)
    }
    
    const { data, error } = await query
    if (error) throw error

    let result = Array.isArray(data) ? data : []

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
    const { data, error } = await supabase
      .from('positions')
      .select('*')
      .eq('id', id)
      .single()
      
    if (error) throw error
    return data
  },

  // 获取考试时间线
  async getExamTimeline(provinceCode, year) {
    try {
      const { data, error } = await supabase
        .from('exam_timelines')
        .select('*')
        .eq('province_code', provinceCode)
        .eq('year', year)
        .single()

      if (error || !data) {
        console.warn('未找到时间线数据，使用模拟数据', error)
        // 返回模拟数据
        return {
          signup_start: '2026-01-22',
          signup_end: '2026-01-26',
          payment_end: '2026-01-28',
          admit_card_start: '2026-02-20',
          exam_date: '2026-02-25',
          score_date: '2026-03-20',
          interview_date_start: '2026-04-15'
        }
      }
      return data
    } catch (e) {
      console.error('获取时间线失败', e)
      return null
    }
  },

  // 获取数据更新统计信息
  async getUpdateStats() {
    const { data, error } = await supabase
      .from('positions')
      .select('*')

    if (error) throw error
    const list = Array.isArray(data) ? data : []
    return {
      lastUpdateTime: '',
      newPositionsCount: 0,
      totalPositionsCount: list.length,
      updatedProvinces: []
    }
  },

  // 获取更新日志列表
  async getUpdateLogs() {
    return []
  },
  
  // 提交报错反馈
  async submitReport(reportData) {
    console.log('调用 submitReport 方法:', reportData);
    try {
      const data = {
        position_id: reportData.position_id,
        position_name: reportData.position_name,
        report_type: reportData.report_type,
        description: reportData.description,
        user_ip: reportData.user_ip || ''
      };
      
      console.log('发送 POST 请求:', { data });
      
      // 直接使用 uni.request 发送 POST 请求
      return new Promise((resolve, reject) => {
        uni.request({
          url: 'https://hubbzosfrhxnzwuiitcv.supabase.co/rest/v1/report_feedback',
          method: 'POST',
          header: {
            'apikey': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh1YmJ6b3Nmcmh4bnp3dWlpdGN2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjkzNDI4NTEsImV4cCI6MjA4NDkxODg1MX0.Xvo9xHl6jyNcbjoImq4phJnR0Na1zUGpQWLnGTNLsfo',
            'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh1YmJ6b3Nmcmh4bnp3dWlpdGN2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjkzNDI4NTEsImV4cCI6MjA4NDkxODg1MX0.Xvo9xHl6jyNcbjoImq4phJnR0Na1zUGpQWLnGTNLsfo',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          data: data,
          success: (res) => {
            console.log('收到响应:', res);
            if (res.statusCode >= 200 && res.statusCode < 300) {
              resolve(res.data);
            } else {
              reject(new Error(`请求失败: ${res.statusCode} ${res.data?.message || '未知错误'}`));
            }
          },
          fail: (err) => {
            console.error('请求失败:', err);
            reject(err);
          }
        });
      });
    } catch (e) {
      console.error('提交反馈异常:', e);
      throw e;
    }
  }
}
