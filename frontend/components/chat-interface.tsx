"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ArrowLeft, Send, Loader2, Database } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { motion, AnimatePresence } from "framer-motion"
import MarkdownMessage from "@/components/markdown-message"

// Update the ChatInterface props to include file information
interface ChatInterfaceProps {
  title: string
  messages: { role: string; content: string }[]
  agentState: string
  onSendMessage: (message: string) => void
  onBack: () => void
  agentColor?: "cyan" | "purple" | "green"
  files?: {
    count: number
    names: string[]
    totalSize: number
  }
}

export default function ChatInterface({
  title,
  messages,
  agentState,
  onSendMessage,
  onBack,
  agentColor = "cyan",
  files,
}: ChatInterfaceProps) {
  const [message, setMessage] = useState("")
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!message.trim()) return

    onSendMessage(message)
    setMessage("")
  }

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  // Get color based on agent type
  const getColorClasses = () => {
    switch (agentColor) {
      case "purple":
        return {
          badge: "bg-purple-500/20 text-purple-300 border-purple-500/30",
          userBubble: "bg-gradient-to-br from-purple-500 to-pink-500 text-white",
          agentBubble: "bg-gray-800/80 border border-gray-700 text-gray-200",
          pulseColor: "text-purple-400",
          inputFocus: "focus:border-purple-400 focus:ring-purple-400/20",
          button:
            "bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 shadow-purple-500/20",
          filesBadge: "bg-purple-500/10 border-purple-500/30 text-purple-300",
        }
      case "green":
        return {
          badge: "bg-green-500/20 text-green-300 border-green-500/30",
          userBubble: "bg-gradient-to-br from-green-500 to-emerald-500 text-white",
          agentBubble: "bg-gray-800/80 border border-gray-700 text-gray-200",
          pulseColor: "text-green-400",
          inputFocus: "focus:border-green-400 focus:ring-green-400/20",
          button:
            "bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 shadow-green-500/20",
          filesBadge: "bg-green-500/10 border-green-500/30 text-green-300",
        }
      default: // cyan
        return {
          badge: "bg-cyan-500/20 text-cyan-300 border-cyan-500/30",
          userBubble: "bg-gradient-to-br from-cyan-500 to-blue-500 text-white",
          agentBubble: "bg-gray-800/80 border border-gray-700 text-gray-200",
          pulseColor: "text-cyan-400",
          inputFocus: "focus:border-cyan-400 focus:ring-cyan-400/20",
          button: "bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 shadow-cyan-500/20",
          filesBadge: "bg-cyan-500/10 border-cyan-500/30 text-cyan-300",
        }
    }
  }

  const colors = getColorClasses()

  // Format file size to human-readable format
  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + " B"
    else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB"
    else return (bytes / 1048576).toFixed(1) + " MB"
  }

  return (
    <Card className="flex flex-col h-[80vh] border-0 bg-gray-800/30 backdrop-blur-md shadow-xl overflow-hidden border-t border-gray-700/50">
      <CardHeader className="flex flex-row items-center justify-between py-4 border-b border-gray-700/50">
        <div className="flex items-center space-x-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={onBack}
            className="text-gray-400 hover:text-white hover:bg-gray-700/50"
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <CardTitle className="text-white">{title}</CardTitle>
        </div>
        <div className="flex items-center gap-2">
          {files && (
            <motion.div
              initial={{ opacity: 0, scale: 0.8, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              transition={{ type: "spring", stiffness: 300, damping: 20 }}
              className={`flex items-center gap-1.5 px-2 py-1 rounded-md border ${colors.filesBadge}`}
            >
              <Database className={`h-3.5 w-3.5 ${colors.pulseColor}`} />
              <span className="text-xs font-medium">
                {files.count} file{files.count !== 1 ? "s" : ""} ({formatFileSize(files.totalSize)})
              </span>
            </motion.div>
          )}
          <AnimatePresence mode="wait">
            {agentState !== "idle" && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.2 }}
              >
                <Badge variant="outline" className={`animate-pulse ${colors.badge}`}>
                  <Loader2 className={`h-3 w-3 mr-1 animate-spin ${colors.pulseColor}`} />
                  {agentState}
                </Badge>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </CardHeader>

      <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
        {files && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            transition={{ duration: 0.3 }}
            className="mb-4"
          >
            <div className={`p-3 rounded-lg border ${colors.filesBadge} bg-gray-800/50`}>
              <div className="flex items-center gap-2 mb-2">
                <Database className={`h-4 w-4 ${colors.pulseColor}`} />
                <h4 className="text-sm font-medium">Uploaded Files</h4>
                <div className="ml-auto text-xs text-gray-400">{formatFileSize(files.totalSize)}</div>
              </div>
              <div className="space-y-1">
                {files.names.map((name, index) => (
                  <motion.div
                    key={index}
                    className="text-xs text-gray-300 flex items-center gap-1.5"
                    initial={{ opacity: 0, x: -5 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05, duration: 0.2 }}
                  >
                    <div className="w-1.5 h-1.5 rounded-full bg-gray-500"></div>
                    {name}
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>
        )}

        <AnimatePresence initial={false}>
          {messages.map((msg, index) => (
            <motion.div
              key={index}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.3, delay: 0.1 }}
            >
              <MarkdownMessage content={msg.content} colorClasses={colors} role={msg.role} />
            </motion.div>
          ))}
        </AnimatePresence>
        <div ref={messagesEndRef} />
      </CardContent>

      <div className="p-4 border-t border-gray-700/50 bg-gray-800/50">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <Input
            placeholder="Type a message..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            className={`flex-1 bg-gray-700/50 border-gray-600 text-white ${colors.inputFocus} transition-all duration-300`}
            disabled={agentState !== "idle"}
          />
          <Button
            type="submit"
            disabled={agentState !== "idle"}
            className={`${colors.button} text-white border-0 shadow-lg transition-all duration-300`}
          >
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </div>
    </Card>
  )
}
