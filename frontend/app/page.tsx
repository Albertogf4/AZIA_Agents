"use client"
import { useState } from "react"
import { AnimatePresence } from "framer-motion"
import { useRouter } from "next/navigation"
import HomeScreen from "@/components/home-screen"
import AgentInterface from "@/components/agent-interface"

export default function Home() {
  const [showAgentInterface, setShowAgentInterface] = useState(false)
  const router = useRouter()

  // Function to handle navigation to agent interface
  const navigateToAgentInterface = () => {
    setShowAgentInterface(true)
  }

  return (
  
    <main className="min-h-screen bg-gradient-to-br from-black via-gray-900 to-slate-900 text-white relative overflow-hidden">
      <AnimatePresence mode="wait">
        {!showAgentInterface ? (
          <HomeScreen key="home" onNavigate={navigateToAgentInterface} />
        ) : (
          <AgentInterface key="agent-interface" />
        )}
      </AnimatePresence>
    </main>
  )
}
