"use client"

import { useAuth } from "@/lib/hooks/auth"
import { useRouter } from "next/navigation"
import { useParams } from "next/navigation"
import { useEffect, useState } from "react"
import { apiAuth } from "@/lib/axios"

import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"

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
  const isReady = players.find((p) => p.id === user?.id)?.isReady

  useEffect(() => {
    const token = getAccessToken()
    // 连接到SSE
    const eventSource = new EventSource(
      `http://localhost:8000/sse/room/events?token=${token}&room_id=${id}`,
    )
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === "update") {
        const { players, host, ready } = data.new_state
        setPlayers(
          players.map((playerId: string, index: number) => ({
            id: playerId,
            isHost: playerId === host,
            isReady: ready[playerId] || false,
          })),
        )
      } else if (data.type === "initial") {
        const { players, host, ready } = data.state
        setPlayers(
          players.map((playerId: string, index: number) => ({
            id: playerId,
            isHost: playerId === host,
            isReady: ready[playerId] || false,
          })),
        )
      }
    }
    return () => {
      eventSource.close()
    }
  }, [])

  async function handleReady() {
    // 发送准备请求
    const response = await apiAuth.post("/room/set-ready", {
      is_ready: !isReady,
    })
    console.log("准备响应:", response.data)
  }

  async function handleStartGame() {
    // 发送开始游戏请求
    const token = getAccessToken()
  }

  return (
    <div className="min-h-screen flex justify-center items-center">
      <Card className="p-6 w-full max-w-md mx-auto">
        <h2 className="text-xl font-bold mb-4">房间 {id}</h2>
        <div className="space-y-2 mb-4">
          {players.map((player) => (
            <div
              key={player.id}
              className="flex justify-between items-center p-2 border rounded"
            >
              <span>{player.id}</span>
              {player.isHost && (
                <span className="text-sm text-gray-500">(房主)</span>
              )}
              <span
                className={player.isReady ? "text-green-500" : "text-red-500"}
              >
                {player.isReady ? "已准备" : "未准备"}
              </span>
            </div>
          ))}
        </div>
        <Button
          onClick={isHost ? handleStartGame : handleReady}
          className="w-full"
        >
          {isHost ? "开始游戏" : isReady ? "取消准备" : "准备"}
        </Button>
      </Card>
    </div>
  )
}
