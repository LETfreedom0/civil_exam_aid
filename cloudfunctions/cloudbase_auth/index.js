/**
 * 环境共享鉴权云函数（微信云开发环境共享必需）。
 *
 * 调用方小程序通过 wx.cloud.Cloud({ resourceAppid, resourceEnv }) init 时，
 * 本函数会被自动调用，用于确认是否允许对方使用本环境资源。
 * 返回 errCode: 0 表示授权通过。
 *
 * 注意：函数名必须为 cloudbase_auth，不可改名。
 */
const cloud = require('wx-server-sdk')

cloud.init({
  env: cloud.DYNAMIC_CURRENT_ENV,
})

exports.main = async (event, context) => {
  const wxContext = cloud.getWXContext()

  // wxContext.FROM_APPID 为调用方小程序 appid，
  // 如需精确控制共享对象，可在此按 appid 白名单放行：
  // if (wxContext.FROM_APPID !== 'wx2043ee3578306661') {
  //   return { errCode: -1, errMsg: '未授权的小程序' }
  // }

  return {
    errCode: 0,
    errMsg: '',
    auth: JSON.stringify({
      // 自定义安全规则，按需扩展
      allowAll: true,
    }),
  }
}
