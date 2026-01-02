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
      console.error("Error details:", error.response?.data)
      alert("加入房间失败，请检查房间号是否正确")
    }
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
