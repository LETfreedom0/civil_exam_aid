/**
 * 云函数调用封装（跨小程序环境共享模式）。
 *
 * 数据链路：小程序(appid wx2043ee3578306661)
 *          -> wx.cloud.Cloud(resourceAppid/resourceEnv) 跨小程序共享调用
 *          -> 云开发环境 prod-d1glr7pbd4f1ab2f5（属 wx9e594322f0cef94f）的 gwy-api 云函数
 *          -> Supabase Postgres（连接串在云函数环境变量 DB_CONNECTION_STRING 中）。
 *
 * 前置条件（一次性配置）：
 * 1. 资源方小程序（wx9e594322f0cef94f）云开发控制台「更多 → 环境共享」开通，
 *    添加共享方 wx2043ee3578306661，勾选环境 prod-d1glr7pbd4f1ab2f5 及权限。
 * 2. 资源方环境中已部署 cloudbase_auth 云函数（鉴权用，见 cloudfunctions/cloudbase_auth）。
 *
 * 基础库要求：>= 2.13.0（wx.cloud.Cloud 支持）。
 */

// 云开发环境所属的小程序（资源方）
const RESOURCE_APPID = 'wx9e594322f0cef94f'
// 资源方环境 ID
const CLOUD_ENV = 'prod-d1glr7pbd4f1ab2f5'
// 要调用的云函数名
const FUNCTION_NAME = 'gwy-api'

let cloudInstance = null
let initPromise = null

function ensureCloud() {
  // #ifdef MP-WEIXIN
  if (!wx.cloud) {
    return Promise.reject(new Error('当前基础库不支持云开发，请将基础库升级到 2.13.0 以上'))
  }
  if (!cloudInstance) {
    // 资源复用：跨小程序调用共享环境，必须用 Cloud 实例而非 wx.cloud 直接调用
    cloudInstance = new wx.cloud.Cloud({
      resourceAppid: RESOURCE_APPID,
      resourceEnv: CLOUD_ENV,
    })
    // 跨账号/跨小程序调用必须等待 init 完成（init 过程中资源方的 cloudbase_auth 会被调用鉴权）
    initPromise = cloudInstance.init()
  }
  return initPromise.then(() => cloudInstance)
  // #endif

  // #ifndef MP-WEIXIN
  return Promise.reject(new Error('云函数仅在微信小程序端可用'))
  // #endif
}

/**
 * 调用 gwy-api 云函数。
 * @param {string} action 业务动作，如 getPositions / getStats / submitReport
 * @param {object} [payload] 业务参数
 * @returns {Promise<any>} 云函数返回的 data 字段
 */
export async function callApi(action, payload = {}) {
  const cloud = await ensureCloud()
  const res = await cloud.callFunction({
    name: FUNCTION_NAME,
    data: { action, ...payload },
  })
  const result = res && res.result
  if (result && result.ok) {
    return result.data
  }
  throw new Error((result && result.error) || '云函数返回异常')
}
