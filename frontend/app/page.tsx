"use client"

import { useAuth } from "@/lib/hooks/auth"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import { apiAuth } from "@/lib/axios"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card } from "@/components/ui/card"

export default function Home() {
  const router = useRouter()
  const { user, loading } = useAuth()
  const [inputRoomId, setInputRoomId] = useState("")

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login")
    }
  }, [user, loading, router])

  useEffect(() => {
    if (!loading && user) {
      const fetchPlayerState = async () => {
        try {
          const response = await apiAuth.post("/get-player-state")
          const { player_state } = response.data
          if (
            player_state.status === "in_room" ||
            player_state.status === "in_game"
          ) {
            if (player_state.room_id) {
              router.push(`/room/${player_state.room_id}`)
            }
          }
        } catch (error) {
          console.error("Failed to get player state:", error)
        }
      }
      fetchPlayerState()
    }
  }, [user, loading, router])

  if (loading) {
    return <div>加载中...</div>
  }

  if (!user) {
    return null
  }

  async function handleCreateRoom() {
    const response = await apiAuth.post("/room/create-room")
    const { roomId } = response.data
    router.push(`/room/${roomId}`)
  }

  async function handleJoinRoom() {
    if (inputRoomId.trim() === "") {
      alert("请输入有效的房间号")
      return
    }
    try {
      await apiAuth.post("/room/join-room", { room_id: inputRoomId.trim() })
      router.push(`/room/${inputRoomId.trim()}`)
    } catch (error) {
      console.error("Failed to join room:", error)
      alert("加入房间失败，请检查房间号是否正确")
    }
  }

  function handleRandomMatch() {
    router.push("/lobby/random-match")
  }

  return (
    <div className="min-h-screen flex justify-center items-center">
      <Card className="p-6 w-full max-w-md mx-auto">
        <h2 className="text-xl font-bold mb-4">五子棋</h2>
        <div className="space-y-4">
          <Button onClick={handleCreateRoom} className="w-full">
            创建房间
          </Button>
          <div className="space-y-2">
            <Input
              type="text"
              placeholder="输入房间号加入房间"
              value={inputRoomId}
              onChange={(e) => setInputRoomId(e.target.value)}
              className="w-full p-2 border rounded"
            />
            <Button onClick={handleJoinRoom} className="w-full">
              加入房间
            </Button>
          </div>
          <Button onClick={handleRandomMatch} className="w-full">
            随机匹配
          </Button>
        </div>
      </Card>
    </div>
  )
}
