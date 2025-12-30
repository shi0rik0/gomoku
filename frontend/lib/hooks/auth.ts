import { useEffect, useState } from "react"

export type User = {
  id: string
  name?: string
  email?: string
  // 根据你的 JWT payload 调整
}

const TOKEN_KEY = "access_token"

// 从 JWT 解析用户（含过期检查）
const parseUserFromToken = (token: string | null): User | null => {
  if (!token) return null
  try {
    const payloadBase64 = token.split(".")[1]
    const payload = JSON.parse(
      atob(payloadBase64.replace(/-/g, "+").replace(/_/g, "/")),
    )
    // 检查是否过期
    if (payload.exp && Date.now() >= payload.exp * 1000) {
      console.log("Token 已过期")
      return null
    }
    console.log("解析的用户:", payload)
    return {
      id: payload.sub || payload.id,
      name: payload.name,
      email: payload.email,
    }
  } catch (e) {
    console.log("Token 解析失败:", e)
    return null
  }
}

export function useAuth() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  // 验证当前 token 并更新状态
  const validateToken = () => {
    const token =
      typeof window !== "undefined" ? localStorage.getItem(TOKEN_KEY) : null
    console.log("当前 token:", token)
    const parsedUser = parseUserFromToken(token)
    console.log("解析后的用户:", parsedUser)
    setUser(parsedUser)
    setLoading(false)
  }

  useEffect(() => {
    // 1. 初始验证
    validateToken()

    // 2. 👇 方案 1：监听其他标签页的 localStorage 变化
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === TOKEN_KEY) {
        validateToken() // 重新验证
      }
    }
    window.addEventListener("storage", handleStorageChange)

    // 3. 👇 方案 2：定时检查 token 是否过期（每 2 分钟）
    const interval = setInterval(
      () => {
        const token = localStorage.getItem(TOKEN_KEY)
        const currentUser = parseUserFromToken(token)
        if (!currentUser && user) {
          // 从有效变为无效
          setUser(null)
        } else if (currentUser && !user) {
          // 极少数情况：token 被恢复（如调试）
          setUser(currentUser)
        }
      },
      2 * 60 * 1000,
    ) // 2 分钟检查一次

    // 清理
    return () => {
      window.removeEventListener("storage", handleStorageChange)
      clearInterval(interval)
    }
  }, []) // 注意：依赖 user 是为了在登出后停止定时器

  // 登录：保存 token
  const login = (accessToken: string) => {
    localStorage.setItem(TOKEN_KEY, accessToken)
    const parsedUser = parseUserFromToken(accessToken)
    setUser(parsedUser)
  }

  // 登出：清除 token
  const logout = () => {
    localStorage.removeItem(TOKEN_KEY)
    setUser(null)
  }

  // 获取当前 token（用于 API 请求）
  const getAccessToken = () => {
    return typeof window !== "undefined"
      ? localStorage.getItem(TOKEN_KEY)
      : null
  }

  return { user, loading, login, logout, getAccessToken }
}
