"use client"

import { useRouter } from "next/navigation"

import { api } from "@/lib/axios"

export default function Home() {
  const router = useRouter()

  const onAnonymousLogin = async () => {
    const response = await api.post("/auth/anonymous-login")
    const { accessToken } = response.data
    localStorage.setItem("access_token", accessToken)
    router.push("/lobby")
  }

  return (
    <div>
      <button onClick={onAnonymousLogin}>匿名登录</button>
    </div>
  )
}
