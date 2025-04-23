import { createApp } from 'vue'
import App from './App.vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

const app = createApp(App)
app.use(ElementPlus, {
  locale: zhCn
})
app.mount('#app')

// 添加Vue特性标志
window.__VUE_PROD_HYDRATION_MISMATCH_DETAILS__ = false;
