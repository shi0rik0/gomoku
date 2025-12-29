"use client"

import { useAuth } from "@/lib/hooks/auth"

export default function Home() {
  const { user } = useAuth()

  return <div> </div>
}
