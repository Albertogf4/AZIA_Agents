"use client"
import { useState } from "react"
import { useEffect } from "react"

import GlobalAgent from "@/components/global-agent"
import RagAgent from "@/components/rag-agent"
import WebSearchAgent from "@/components/web-search-agent"
import { motion, AnimatePresence } from "framer-motion"
import ConversationPanel from "@/components/conversation-panel"
import { MessageCircleIcon } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useConversationStore } from "@/lib/conversation-store"


export default function AgentInterface() {
  const [isPanelOpen, setIsPanelOpen] = useState(false)
  const [activeTab, setActiveTab] = useState<"global" | "rag" | "websearch">("global")
  const { conversations, currentConversationId, setCurrentConversationId } = useConversationStore()

  // Set the active tab based on the current conversation when it changes
  useEffect(() => {
    if (currentConversationId && conversations[currentConversationId]) {
      setActiveTab(conversations[currentConversationId].agentType)
    }
  }, [currentConversationId, conversations])

  const handleTabChange = (value: string) => {
    // Cast the value to the correct type
    const newTab = value as "global" | "rag" | "websearch"

    // Set the active tab
    setActiveTab(newTab)

    // Clear the current conversation if it's of a different type
    if (currentConversationId && conversations[currentConversationId]?.agentType !== newTab) {
      setCurrentConversationId(null)
    }
  }

  const togglePanel = () => {
    setIsPanelOpen(!isPanelOpen)
  }

  return (
    <div className="container mx-auto p-4 max-w-5xl pt-10">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="flex justify-between items-center"
      >
        <h1 className="text-4xl font-bold mb-8 bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 to-purple-500">
          AI Agent Interface
        </h1>

        <Button
          variant="ghost"
          size="icon"
          onClick={togglePanel}
          className={`rounded-full p-2 transition-all duration-300 ${
            isPanelOpen
              ? "bg-gray-700/50 text-white"
              : "bg-gray-800/30 text-gray-400 hover:text-white hover:bg-gray-700/50"
          }`}
        >
          <MessageCircleIcon className="h-5 w-5" />
          <span className="sr-only">Toggle conversation history</span>
        </Button>
      </motion.div>

      <div className="w-full">
        <div className="grid grid-cols-3 mb-8 bg-gray-800/50 backdrop-blur-md border border-gray-700 rounded-xl overflow-hidden p-1">
          {[
            { value: "global", label: "Global Agent" },
            { value: "rag", label: "RAG Agent" },
            { value: "websearch", label: "Web Search Agent" },
          ].map((tab, index) => (
            <motion.div
              key={tab.value}
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 * index, duration: 0.5 }}
              className="w-full"
            >
              <button
                onClick={() => handleTabChange(tab.value)}
                className={`w-full py-2 px-4 rounded-lg transition-all duration-300 ${
                  activeTab === tab.value
                    ? "bg-gradient-to-r from-cyan-500/20 to-purple-500/20 text-white shadow-lg backdrop-blur-md"
                    : "text-gray-400 hover:text-gray-200 hover:bg-gray-700/30"
                }`}
              >
                {tab.label}
              </button>
            </motion.div>
          ))}
        </div>

        <AnimatePresence mode="wait">
          {activeTab === "global" && (
            <motion.div
              key="global"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.3 }}
            >
              <GlobalAgent />
            </motion.div>
          )}

          {activeTab === "rag" && (
            <motion.div
              key="rag"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.3 }}
            >
              <RagAgent />
            </motion.div>
          )}

          {activeTab === "websearch" && (
            <motion.div
              key="websearch"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.3 }}
            >
              <WebSearchAgent />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <ConversationPanel
        isOpen={isPanelOpen}
        onClose={() => setIsPanelOpen(false)}
        onSelectConversation={(agentType) => {
          setActiveTab(agentType)
        }}
      />
    </div>
  )
}
