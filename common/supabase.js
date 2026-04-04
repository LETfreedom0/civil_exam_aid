const supabaseUrl = 'https://hubbzosfrhxnzwuiitcv.supabase.co'
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh1YmJ6b3Nmcmh4bnp3dWlpdGN2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjkzNDI4NTEsImV4cCI6MjA4NDkxODg1MX0.Xvo9xHl6jyNcbjoImq4phJnR0Na1zUGpQWLnGTNLsfo'

/**
 * 发送 Supabase PostgREST 请求（兼容微信小程序/uni.request）。
 * @param {string} url 请求地址
 * @param {object} options 请求选项
 * @param {object} [options.headers] 请求头
 * @returns {Promise<{ statusCode: number, data: any, header: any, errMsg?: string }>}
 */
const request = (url, options = {}) => {
  return new Promise((resolve, reject) => {
    uni.request({
      url,
      method: options.method || 'GET',
      data: options.data || void 0,
      header: options.headers || {},
      success: (res) => resolve(res),
      fail: (err) => reject(err)
    })
  })
}

/**
 * 创建一个兼容 supabase-js 风格的 thenable 查询对象。
 */
class RestQuery {
  /**
   * @param {string} table 表名
   */
  constructor(table) {
    this._table = table
    this._select = '*'
    this._filters = []
    this._single = false
    this._method = 'GET'
    this._data = null
  }

  /**
   * @param {string} columns 选择列，默认 '*'
   * @returns {RestQuery}
   */
  select(columns = '*') {
    this._select = columns || '*'
    this._method = 'GET'
    return this
  }

  /**
   * @param {string} column 字段名
   * @param {string|number|boolean|null} value 等值
   * @returns {RestQuery}
   */
  eq(column, value) {
    this._filters.push({ op: 'eq', column, value })
    return this
  }

  /**
   * 期望返回单条对象（等价于 PostgREST object accept）。
   * @returns {RestQuery}
   */
  single() {
    this._single = true
    return this
  }

  /**
   * 插入数据
   * @param {object} data 要插入的数据
   * @returns {RestQuery}
   */
  insert(data) {
    this._method = 'POST'
    this._data = data
    return this
  }

  /**
   * 让查询对象可以被 await（thenable）。
   * @param {(v:any)=>any} resolve
   * @param {(e:any)=>any} reject
   */
  then(resolve, reject) {
    return this._execute().then(resolve, reject)
  }

  /**
   * 执行查询并返回 { data, error }，对齐 supabase-js 的返回结构。
   * @returns {Promise<{data:any, error:any}>}
   */
  async _execute() {
    const baseUrl = `${supabaseUrl}/rest/v1/${encodeURIComponent(this._table)}`
    let url = baseUrl
    let requestOptions = {}

    const headers = {
      apikey: supabaseAnonKey,
      Authorization: `Bearer ${supabaseAnonKey}`
    }
    
    // 根据请求方法设置不同的请求头和请求选项
    if (this._method === 'POST') {
      headers['Content-Type'] = 'application/json'
      requestOptions = {
        method: 'POST',
        headers,
        data: this._data
      }
    } else if (this._method === 'GET') {
      // 对于 GET 请求，设置 Accept 头
      if (this._single) {
        headers.Accept = 'application/vnd.pgrst.object+json'
      } else {
        headers.Accept = 'application/json'
      }
      
      // 构建查询参数
      const params = [`select=${encodeURIComponent(this._select)}`]
      for (const f of this._filters) {
        const key = encodeURIComponent(f.column)
        const val = encodeURIComponent(String(f.value))
        params.push(`${key}=${f.op}.${val}`)
      }
      if (params.length > 0) {
        url = `${baseUrl}?${params.join('&')}`
      }
      
      requestOptions = {
        method: 'GET',
        headers
      }
    }

    try {
      console.log('发送请求:', { url, method: this._method, headers, data: this._data });
      const res = await request(url, requestOptions)
      console.log('收到响应:', { statusCode: res.statusCode, data: res.data, header: res.header });
      
      const ok = res.statusCode >= 200 && res.statusCode < 300
      if (!ok) {
        return {
          data: null,
          error: { status: res.statusCode, message: typeof res.data === 'string' ? res.data : res.errMsg || 'Request failed' }
        }
      }
      return { data: res.data, error: null }
    } catch (err) {
      console.error('请求异常:', err);
      return { data: null, error: { status: 0, message: err.errMsg || err.message || 'Network error' } }
    }
  }
}

export const supabase = {
  supabaseUrl,
  /**
   * @param {string} table 表名
   * @returns {RestQuery}
   */
  from(table) {
    return new RestQuery(table)
  }
}
