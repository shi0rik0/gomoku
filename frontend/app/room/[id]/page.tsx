"use client"

import { useAuth } from "@/lib/hooks/auth"
import { useRouter } from "next/navigation"
import { useParams } from "next/navigation"
import { useEffect, useState } from "react"
import { apiAuth } from "@/lib/axios"

export default function Home() {
  const { id } = useParams()
  const router = useRouter()
  const { user, loading, getAccessToken } = useAuth()

  const [players, setPlayers] = useState([
    {
      id: "player1",
      isHost: true,
      isReady: true,
    },
    {
      id: "player2",
      isHost: false,
      isReady: false,
    },
  ])

  const isHost = user?.id === players.find((p) => p.isHost)?.id

  useEffect(() => {
    const token = getAccessToken()
    // 连接到SSE
    const eventSource = new EventSource(
      `http://localhost:8000/lobby/events?token=${token}&room_id=${id}`,
    )
    eventSource.onmessage = (event) => {
      const { state } = JSON.parse(event.data)
      const { players, host, ready } = state
      setPlayers(
        players.map((playerId: string, index: number) => ({
          id: playerId,
          isHost: playerId === host,
          isReady: ready[index],
        })),
      )
    }
    return () => {
      eventSource.close()
    }
  }, [])

  async function handleReady() {
    // 发送准备请求
    const response = await apiAuth.post("/lobby/set-ready", {
      room_id: id,
      is_ready: true,
    })
    console.log("准备响应:", response.data)
  }

  async function handleStartGame() {
    // 发送开始游戏请求
    const token = getAccessToken()
  }

  return (
    <div>
      {players.map((player) => (
        <div key={player.id}>
          <span>{player.id}</span>
          {player.isHost && <span> (房主) </span>}
          <span> - </span>
          <span>{player.isReady ? "已准备" : "未准备"}</span>
        </div>
      ))}
      <div>
        <button onClick={isHost ? handleStartGame : handleReady}>
          {isHost ? "开始游戏" : "准备"}
        </button>
      </div>
    </div>
  )
}
