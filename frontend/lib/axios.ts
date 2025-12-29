import axios from "axios"

// 递归函数：将对象键从 snake_case 转换为 camelCase
function toCamelCase(obj: any): any {
  if (obj === null || typeof obj !== "object") return obj
  if (Array.isArray(obj)) return obj.map(toCamelCase)
  const result: any = {}
  for (const key in obj) {
    if (obj.hasOwnProperty(key)) {
      const camelKey = key.replace(/_([a-z])/g, (_, letter) =>
        letter.toUpperCase(),
      )
      result[camelKey] = toCamelCase(obj[key])
    }
  }
  return result
}

// 创建axios实例
const apiAuth = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE, // 后端API的基础URL
})

// 请求拦截器：自动添加JWT token
apiAuth.interceptors.request.use(
  (config) => {
    // 从localStorage获取token
    const token = localStorage.getItem("access_token")
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  },
)

// 响应拦截器：自动转换字段名并处理401错误
apiAuth.interceptors.response.use(
  (response) => {
    // 转换响应数据中的字段名
    if (response.data && typeof response.data === "object") {
      response.data = toCamelCase(response.data)
    }
    return response
  },
  (error) => {
    if (error.response?.status === 401) {
      // 处理未授权错误，例如清除token并重定向到登录页
      localStorage.removeItem("access_token")
      // 可以添加重定向逻辑
    }
    return Promise.reject(error)
  },
)

// 不需要身份认证的 API
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE,
})

// 为 api 实例也添加响应拦截器以转换字段名
api.interceptors.response.use(
  (response) => {
    // 转换响应数据中的字段名
    if (response.data && typeof response.data === "object") {
      response.data = toCamelCase(response.data)
    }
    return response
  },
  (error) => {
    return Promise.reject(error)
  },
)

export { apiAuth, api }
