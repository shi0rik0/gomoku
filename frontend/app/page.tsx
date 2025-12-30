"use client"

import { useAuth } from "@/lib/hooks/auth"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import { apiAuth } from "@/lib/axios"

export default function Home() {
  const router = useRouter()
  const { user, loading, getAccessToken } = useAuth()
  const [inputRoomId, setInputRoomId] = useState("")

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login")
    }
  }, [user, loading, router])

  if (loading) {
    return <div>加载中...</div>
  }

  if (!user) {
    return null
  }

  async function handleCreateRoom() {
    const response = await apiAuth.post("/lobby/create-room")
    const { roomId } = response.data
    router.push(`/room/${roomId}`)
  }

  function handleJoinRoom() {
    if (inputRoomId.trim() === "") {
      alert("请输入有效的房间号")
      return
    }
    router.push(`/room/${inputRoomId.trim()}`)
  }

  function handleRandomMatch() {
    router.push("/lobby/random-match")
  }

  return (
    <div>
      <p>{getAccessToken()}</p>
      <div>
        <button onClick={handleCreateRoom}>创建房间</button>
      </div>
      <div>
        <input
          type="text"
          placeholder="输入房间号加入房间"
          value={inputRoomId}
          onChange={(e) => setInputRoomId(e.target.value)}
        />
        <button onClick={handleJoinRoom}>加入房间</button>
      </div>
      <div>
        <button onClick={handleRandomMatch}>随机匹配</button>
      </div>
    </div>
  )
}
