"use client"

import { motion, AnimatePresence } from "framer-motion"
import { X, MessageCircle, Sparkles, BookOpen, Globe } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useConversationStore } from "@/lib/conversation-store"
import { formatDistanceToNow } from "date-fns"

interface ConversationPanelProps {
  isOpen: boolean
  onClose: () => void
  onSelectConversation: (agentType: "global" | "rag" | "websearch") => void
}

export default function ConversationPanel({ isOpen, onClose, onSelectConversation }: ConversationPanelProps) {
  const { conversations, currentConversationId, setCurrentConversationId } = useConversationStore()

  const getAgentIcon = (agentType: string) => {
    switch (agentType) {
      case "global":
        return <Sparkles className="h-4 w-4 text-cyan-400" />
      case "rag":
        return <BookOpen className="h-4 w-4 text-purple-400" />
      case "websearch":
        return <Globe className="h-4 w-4 text-green-400" />
      default:
        return <MessageCircle className="h-4 w-4 text-gray-400" />
    }
  }

  const getAgentColor = (agentType: string) => {
    switch (agentType) {
      case "global":
        return "from-cyan-500/10 to-blue-500/10 border-cyan-500/20"
      case "rag":
        return "from-purple-500/10 to-pink-500/10 border-purple-500/20"
      case "websearch":
        return "from-green-500/10 to-emerald-500/10 border-green-500/20"
      default:
        return "from-gray-500/10 to-gray-600/10 border-gray-500/20"
    }
  }

  const conversationArray = Object.entries(conversations)
    .map(([id, conversation]) => ({ id, ...conversation }))
    .sort((a, b) => b.timestamp - a.timestamp)

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 bg-black/40 backdrop-blur-sm z-40 lg:hidden"
            onClick={onClose}
          />

          {/* Panel */}
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="fixed top-0 right-0 h-full w-80 md:w-96 bg-gray-900/95 backdrop-blur-md border-l border-gray-700/50 shadow-2xl z-50 overflow-hidden"
          >
            <div className="flex flex-col h-full">
              <div className="flex items-center justify-between p-4 border-b border-gray-700/50">
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  <MessageCircle className="h-5 w-5 text-purple-400" />
                  Conversations
                </h2>
                <Button variant="ghost" size="icon" onClick={onClose} className="text-gray-400 hover:text-white">
                  <X className="h-5 w-5" />
                </Button>
              </div>

              <div className="flex-1 overflow-y-auto p-3 space-y-3">
                {conversationArray.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-full text-center p-6 text-gray-500">
                    <MessageCircle className="h-12 w-12 mb-3 opacity-20" />
                    <p className="text-lg font-medium">No conversations yet</p>
                    <p className="text-sm">Start chatting with an agent to create a conversation history</p>
                  </div>
                ) : (
                  conversationArray.map((conversation, index) => (
                    <motion.div
                      key={conversation.id}
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05, duration: 0.3 }}
                      className={`p-3 rounded-lg cursor-pointer border bg-gradient-to-r ${getAgentColor(
                        conversation.agentType,
                      )} transition-all duration-300 hover:bg-gray-800/70 ${
                        currentConversationId === conversation.id ? "ring-2 ring-purple-500/50" : ""
                      }`}
                      onClick={() => {
                        setCurrentConversationId(conversation.id)
                        onSelectConversation(conversation.agentType)
                        onClose()
                      }}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        {getAgentIcon(conversation.agentType)}
                        <span className="text-sm font-medium text-gray-300">
                          {conversation.agentType === "global"
                            ? "Global Agent"
                            : conversation.agentType === "rag"
                              ? "RAG Agent"
                              : "Web Search Agent"}
                        </span>
                      </div>
                      <h3 className="text-white font-medium mb-1 line-clamp-1">{conversation.title}</h3>
                      <div className="flex justify-between items-center">
                        <p className="text-xs text-gray-400">
                          {conversation.messages.length} message{conversation.messages.length !== 1 ? "s" : ""}
                        </p>
                        <p className="text-xs text-gray-500">
                          {formatDistanceToNow(conversation.timestamp, { addSuffix: true })}
                        </p>
                      </div>
                    </motion.div>
                  ))
                )}
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
