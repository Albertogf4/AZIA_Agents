"use client"

import type React from "react"

import { useState, useEffect, useRef } from "react"
import { sendChatMessage, uploadFiles, generateVectorDb as apiGenerateVectorDb } from "@/lib/api-service"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import { Database, Send, BookOpen } from "lucide-react"
import FileUpload from "@/components/file-upload"
import ChatInterface from "@/components/chat-interface"
import { motion, AnimatePresence } from "framer-motion"
import { useConversationStore } from "@/lib/conversation-store"

// Update the RagAgent component to handle file transitions
export default function RagAgent() {
  const [message, setMessage] = useState("")
  const [showChat, setShowChat] = useState(false)
  const [agentState, setAgentState] = useState("idle")
  const [files, setFiles] = useState<File[]>([])
  const [vectorDbGenerated, setVectorDbGenerated] = useState(false)
  const [dbIconPosition, setDbIconPosition] = useState({ x: 0, y: 0 })
  const dbButtonRef = useRef<HTMLButtonElement>(null)
  const [uploadedFiles, setUploadedFiles] = useState<{ name: string; path: string; size: number }[]>([]);
  const [currentStage, setCurrentStage] = useState(0)

  const {
    conversations,
    currentConversationId,
    addConversation,
    addMessage,
    getCurrentConversation,
    updateConversationFiles,
  } = useConversationStore()

  // Initialize conversation or load existing one
  useEffect(() => {
    const currentConversation = getCurrentConversation()

    // If we have a current conversation of the right type, show the chat
    if (currentConversation && currentConversation.agentType === "rag" && currentConversation.messages.length > 0) {
      setShowChat(true)

      // If the conversation has files, update our local state
      if (currentConversation.files) {
        setVectorDbGenerated(true)
      }
    } else {
      // If we don't have a current conversation or it's not the right type, don't show chat
      setShowChat(false)
    }
  }, [currentConversationId, conversations, getCurrentConversation])

  // Capture the position of the database button for animation
  useEffect(() => {
    if (dbButtonRef.current && vectorDbGenerated) {
      const rect = dbButtonRef.current.getBoundingClientRect()
      setDbIconPosition({
        x: rect.left + rect.width / 2,
        y: rect.top + rect.height / 2,
      })
    }
  }, [vectorDbGenerated, files.length])

  // Function to handle transitioning to chat view with animation
  const transitionToChat = (conversationId: string) => {
    // If we have files and a vector DB, capture the position for animation
    if (files.length > 0 && vectorDbGenerated && dbButtonRef.current) {
      const rect = dbButtonRef.current.getBoundingClientRect()
      setDbIconPosition({
        x: rect.left + rect.width / 2,
        y: rect.top + rect.height / 2,
      })

      // Create a temporary floating icon that animates to the corner
      const floatingIcon = document.createElement("div")
      floatingIcon.className = "fixed z-50 bg-purple-500 rounded-full p-2 shadow-lg shadow-purple-500/30"
      floatingIcon.style.position = "fixed"
      floatingIcon.style.left = `${rect.left + rect.width / 2 - 16}px`
      floatingIcon.style.top = `${rect.top + rect.height / 2 - 16}px`
      floatingIcon.innerHTML =
        '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" class="text-white"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg>'
      document.body.appendChild(floatingIcon)

      // Animate using GSAP or simple CSS transition
      setTimeout(() => {
        floatingIcon.style.transition = "all 0.8s cubic-bezier(0.2, 0.8, 0.2, 1)"
        floatingIcon.style.left = `${window.innerWidth - 60}px`
        floatingIcon.style.top = `80px`
        floatingIcon.style.transform = "scale(0.8)"

        setTimeout(() => {
          floatingIcon.style.opacity = "0"
          setTimeout(() => {
            document.body.removeChild(floatingIcon)
          }, 300)
        }, 800)
      }, 100)
    }

    // Show the chat view
    setShowChat(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!message.trim()) return

    // Create a new conversation if needed
    let conversationId = currentConversationId
    if (!conversationId || !conversations[conversationId] || conversations[conversationId].agentType !== "rag") {
      conversationId = addConversation("rag")

      // If we have files, add them to the conversation
      if (files.length > 0 && vectorDbGenerated) {
        const fileInfo = {
          count: files.length,
          names: files.map((f) => f.name),
          totalSize: files.reduce((total, file) => total + file.size, 0),
        }
        updateConversationFiles(conversationId, fileInfo)
      }
    }

    // Add user message to chat
    const userMessage = { role: "user", content: message }
    addMessage(conversationId, userMessage)

    // Simulate agent processing
    setAgentState("retrieving relevant documents")

    try {
      const data = await sendChatMessage(
        message,
        conversationId,
        "rag"
      )
      if (data.status === "success") {
        addMessage(conversationId, {
          role: "assistant",
          content: data.response,      // e.g. “Received: <your message>”
        })
      } else {
        addMessage(conversationId, {
          role: "assistant",
          content: `Error: ${data.response || "unknown"}`,
        })
      }
    } catch (err) {
      console.error("RAG chat error:", err)
      addMessage(conversationId, {
        role: "assistant",
        content: "😞 Sorry, something went wrong.",
      })
    } finally {
      setAgentState("idle")
      setMessage("")
      transitionToChat(conversationId)
    }

    // Simulate agent response after a delay
    /*
    setTimeout(() => {
      setAgentState("generating response")

      setTimeout(() => {
        const assistantMessage = {
          role: "assistant",
          content: "Based on your documents, I found that: " + message,
        }
        addMessage(conversationId, assistantMessage)
        setAgentState("idle")
      }, 1500)
    }, 1500)*/
  }

  // Function to generate the vector database
  const generateVectorDb = async () => {
    if (files.length === 0) return
  
    // 1️⃣ Make sure we have a RAG conversation
    let convId = currentConversationId
    if (!convId || conversations[convId]?.agentType !== "rag") {
      convId = addConversation("rag")
    }
  
    // 2️⃣ Enter loading state
    setAgentState("generating vector database")
  
    // 3️⃣ Start your little progress animation
    const stages = [
      "Uploading files",
      "Creating embeddings",
      "Building database",
      "Database ready, connecting it to agent",
    ]
    let idx = 0
    const animate = () => {
      if (idx < stages.length) {
        setCurrentStage(idx++)
        setTimeout(animate, 200)
      }
    }
    animate()
  
    try {
      // 4️⃣ First, upload the raw File[] and get back { name, path, size }[]
      const uploadResp = await uploadFiles(files, convId, "rag")
      animate()
      if (uploadResp.status !== "success") {
        console.error("Upload failed:", uploadResp.message)
        return
      }
      const filePaths = uploadResp.files
      
      // 5️⃣ (Optional) persist those paths into your conversation store
      updateConversationFiles(convId, {
        count: filePaths.length,
        names: filePaths.map((f: any) => f.name),
        totalSize: filePaths.reduce((sum: number, f: any) => sum + f.size, 0),
      })
      animate()
      // 6️⃣ Now call the vector-DB builder
      const dbResp = await apiGenerateVectorDb(filePaths, convId, "rag")
      if (dbResp.status === "success") {
        setVectorDbGenerated(true)
        animate()
        animate()
      } else {
        console.error("Vector DB error:", dbResp.message)
      }
    } catch (err) {
      console.error("Error in generateVectorDb:", err)
    } finally {
      // 7️⃣ Done—reset state
      setAgentState("idle")
    }
  }
  /*const generateVectorDb = () => {
    if (files.length === 0) return

    setAgentState("generating vector database")
    setVectorDbGenerated(false)

    // Track progress stages
    const stages = ["Analyzing files", "Creating embeddings", "Building index", "Optimizing database", "Finalizing"]

    // Start the staged animation process
    let stageIndex = 0
    const processStages = () => {
      if (stageIndex < stages.length) {
        setCurrentStage(stageIndex)
        setTimeout(() => {
          stageIndex++
          processStages()
        }, 800) // Time for each stage
      } else {
        // All stages complete
        setVectorDbGenerated(true)

        // Create file info for the conversation
        const fileInfo = {
          count: files.length,
          names: files.map((f) => f.name),
          totalSize: files.reduce((total, file) => total + file.size, 0),
        }

        // If we have a current conversation, update it with file info
        if (currentConversationId && conversations[currentConversationId]?.agentType === "rag") {
          updateConversationFiles(currentConversationId, fileInfo)
        }

        setAgentState("idle")
      }
    }

    // Start the process
    processStages()
  }*/

  const handleUpload = async () => {
    if (files.length === 0) return
  
    // 1️⃣ Ensure we have a "rag" conversation
    let conversationId = currentConversationId
    if (
      !conversationId ||
      conversations[conversationId]?.agentType !== "rag"
    ) {
      conversationId = addConversation("rag")
    }
  
    // 2️⃣ Show uploading state
    setAgentState("uploading")
    try {
      // 3️⃣ Call the real uploadFiles helper
      const resp = await uploadFiles(files, conversationId, "rag")
  
      if (resp.status === "success") {
        // 4️⃣ Save the returned file list to local state
        setUploadedFiles(resp.files)
  
        // 5️⃣ Update conversation metadata
        updateConversationFiles(conversationId, {
          count: resp.files.length,
          names: resp.files.map((f: any) => f.name),
          totalSize: resp.files.reduce(
            (sum: number, f: any) => sum + f.size,
            0
          ),
        })
  
        // 6️⃣ Now you can allow vector-DB steps
        setVectorDbGenerated(true)
      } else {
        console.error("Upload error:", resp.message)
      }
    } catch (err) {
      console.error("Upload exception:", err)
    } finally {
      // 7️⃣ Always reset to idle when done
      setAgentState("idle")
    }
  }
  

  const handleFileChange = (newFiles: File[]) => {
    setFiles(newFiles)
    setVectorDbGenerated(false)
  }

  const currentConversation = getCurrentConversation()
  const messages = currentConversation?.agentType === "rag" ? currentConversation.messages : []
  const conversationFiles = currentConversation?.agentType === "rag" ? currentConversation.files : undefined

  return (
    <AnimatePresence mode="wait">
      {!showChat ? (
        <motion.div
          key="input"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.5 }}
          className="space-y-6"
        >
          <Card className="border-0 bg-gray-800/30 backdrop-blur-md shadow-xl overflow-hidden border-t border-gray-700/50">
            <CardContent className="pt-6">
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2, duration: 0.5 }}>
                <h2 className="text-2xl font-bold mb-2 flex items-center gap-2 text-purple-300">
                  <BookOpen className="h-5 w-5" />
                  RAG Agent
                </h2>
                <p className="mb-6 text-gray-400">
                  Upload documents and ask questions about their content using Retrieval-Augmented Generation.
                </p>
              </motion.div>

              <div className="space-y-6">
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3, duration: 0.5 }}
                >
                  <FileUpload onFilesChange={handleFileChange} />
                </motion.div>

                {files.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.3 }}
                  >
                    <Button
                      ref={dbButtonRef}
                      onClick={generateVectorDb}
                      //disabled={agentState === "uploading"}
                      className="w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white border-0 shadow-lg shadow-purple-500/20 transition-all duration-300"
                      disabled={agentState === "generating vector database" || files.length===0 || vectorDbGenerated}
                    >
                      {agentState === "generating vector database" ? (
                        <div className="flex items-center justify-center w-full">
                          <div className="relative w-full">
                            <div className="flex items-center justify-between">
                              <motion.div
                                className="flex items-center"
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                transition={{ duration: 0.3 }}
                              >
                                <svg
                                  className="animate-spin -ml-1 mr-3 h-4 w-4 text-white"
                                  xmlns="http://www.w3.org/2000/svg"
                                  fill="none"
                                  viewBox="0 0 24 24"
                                >
                                  <circle
                                    className="opacity-25"
                                    cx="12"
                                    cy="12"
                                    r="10"
                                    stroke="currentColor"
                                    strokeWidth="4"
                                  ></circle>
                                  <path
                                    className="opacity-75"
                                    fill="currentColor"
                                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                                  ></path>
                                </svg>
                                <span className="text-xs font-medium">
                                  {
                                    [
                                      "Uploading files",
                                      "Processing files",
                                      "Creating embeddings",
                                      "Generating database",
                                      "Connecting database to agent",
                                    ][currentStage]
                                  }
                                </span>
                              </motion.div>
                              <span className="text-xs">{Math.min(100, (currentStage) * 25)}%</span>
                            </div>
                            <div className="mt-1.5 w-full bg-purple-900/30 rounded-full h-1.5 overflow-hidden">
                              <motion.div
                                className="h-full bg-white"
                                initial={{ width: "0%" }}
                                animate={{ width: `${Math.min(100, (currentStage) * 25)}%` }}
                                transition={{ duration: 0.5 }}
                              />
                            </div>
                          </div>
                        </div>
                      ) : (
                        <>
                          <Database className="mr-2 h-4 w-4" />
                          {vectorDbGenerated ? "Vector Database Generated" : "Generate Vector Database"}
                        </>
                      )}
                    </Button>
                  </motion.div>
                )}

                <motion.form
                  onSubmit={handleSubmit}
                  className="flex gap-2"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4, duration: 0.5 }}
                >
                  <Input
                    placeholder="Ask about your documents..."
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    className="flex-1 bg-gray-700/50 border-gray-600 text-white focus:border-purple-400 focus:ring-purple-400/20 transition-all duration-300"
                  />
                  <Button
                    type="submit"
                    className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white border-0 shadow-lg shadow-purple-500/20 transition-all duration-300"
                  >
                    <Send className="h-4 w-4" />
                  </Button>
                </motion.form>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      ) : (
        <motion.div
          key="chat"
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          transition={{ duration: 0.5 }}
        >
          {vectorDbGenerated && dbIconPosition.x !== 0 && !showChat && (
            <motion.div
              className="fixed z-50 bg-purple-500 rounded-full p-2 shadow-lg shadow-purple-500/30"
              initial={{
                x: dbIconPosition.x,
                y: dbIconPosition.y,
                scale: 1,
              }}
              animate={{
                x: window.innerWidth - 100,
                y: 80,
                scale: 0.8,
              }}
              transition={{
                type: "spring",
                stiffness: 300,
                damping: 20,
                duration: 0.8,
              }}
            >
              <Database className="h-5 w-5 text-white" />
            </motion.div>
          )}

      <ChatInterface
        title="RAG Agent"
        messages={messages}
        agentState={agentState}
        files={conversationFiles}
        onSendMessage={async (newMessage) => {
          // Crear una conversación si es necesario
          let conversationId = currentConversationId
          if (
            !conversationId ||
            !conversations[conversationId] ||
            conversations[conversationId].agentType !== "rag"
          ) {
            conversationId = addConversation("rag")

            // Agregar la información de archivos si existen y el vector DB se ha generado
            if (files.length > 0 && vectorDbGenerated) {
              const fileInfo = {
                count: files.length,
                names: files.map((f) => f.name),
                totalSize: files.reduce((total, file) => total + file.size, 0),
              }
              updateConversationFiles(conversationId, fileInfo)
            }
          }

          // Agregar el mensaje del usuario
          addMessage(conversationId, { role: "user", content: newMessage })

          // Indicar que el agente está procesando la petición
          setAgentState("retrieving relevant documents")

          try {
            // Enviar el mensaje a la API usando sendChatMessage
            const data = await sendChatMessage(newMessage, conversationId, "rag")
            if (data.status === "success") {
              addMessage(conversationId, { role: "assistant", content: data.response })
            } else {
              addMessage(conversationId, { role: "assistant", content: `Error: ${data.response || "unknown"}` })
            }
          } catch (err) {
            console.error("RAG chat error:", err)
            addMessage(conversationId, { role: "assistant", content: "😞 Sorry, something went wrong." })
          } finally {
            setAgentState("idle")
          }
        }}
        onBack={() => setShowChat(false)}
        agentColor="purple"
      />
        </motion.div>
      )}
    </AnimatePresence>
  )
}
