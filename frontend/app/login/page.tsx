"use client"

import { useRouter } from "next/navigation"

import { api } from "@/lib/axios"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"

export default function Home() {
  const router = useRouter()

  const onAnonymousLogin = async () => {
    const response = await api.post("/auth/login-anonymous")
    const { accessToken } = response.data
    localStorage.setItem("access_token", accessToken)
    router.replace("/")
  }

  return (
    <div className="min-h-screen flex justify-center items-center">
      <Card className="p-6 w-full max-w-md mx-auto">
        <h2 className="text-xl font-bold mb-4">登录</h2>
        <Button onClick={onAnonymousLogin} className="w-full">
          匿名登录
        </Button>
      </Card>
    </div>
  )
}
