<script>
	export default {
		globalData: {
			statusBarHeight: 0,
			navBarHeight: 44,
			menuButtonTop: 0,
			menuButtonHeight: 0,
			customNavBarHeight: 0
		},
		onLaunch: function() {
			console.log('App Launch')
			this.initSafeArea()
		},
		onShow: function() {
			console.log('App Show')
		},
		onHide: function() {
			console.log('App Hide')
		},
		methods: {
			initSafeArea() {
				try {
					const systemInfo = uni.getSystemInfoSync()
					this.globalData.statusBarHeight = systemInfo.statusBarHeight || 20
					
					// #ifdef MP-WEIXIN
					const menuButton = uni.getMenuButtonBoundingClientRect()
					if (menuButton) {
						this.globalData.menuButtonTop = menuButton.top
						this.globalData.menuButtonHeight = menuButton.height
						const menuButtonBottom = menuButton.top + menuButton.height
						const navBarHeight = menuButtonBottom - this.globalData.statusBarHeight + (menuButton.top - this.globalData.statusBarHeight)
						this.globalData.customNavBarHeight = this.globalData.statusBarHeight + navBarHeight
					} else {
						this.globalData.customNavBarHeight = this.globalData.statusBarHeight + 44
					}
					// #endif
					
					// #ifndef MP-WEIXIN
					this.globalData.customNavBarHeight = this.globalData.statusBarHeight + 44
					// #endif
				} catch (e) {
					console.warn('获取安全区域失败，使用默认值', e)
					this.globalData.statusBarHeight = 20
					this.globalData.customNavBarHeight = 64
				}
			}
		}
	}
</script>

<style>
	/*每个页面公共css */
</style>
