"use client"

import type React from "react"

import { useState, useEffect, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import { Search, Globe, Lightbulb, ChevronDown, ChevronUp } from "lucide-react"
import ChatInterface from "@/components/chat-interface"
import { motion, AnimatePresence } from "framer-motion"
import { useConversationStore } from "@/lib/conversation-store"
import { sendChatMessage_Schema } from "@/lib/api-service"
import { Textarea } from "@/components/ui/textarea"

export default function WebSearchAgent() {
  const [message, setMessage] = useState("")
  const [showChat, setShowChat] = useState(false)
  const [agentState, setAgentState] = useState("idle")
  const [schema, setSchema] = useState("")
  const [showSchemaInput, setShowSchemaInput] = useState(false)
  const schemaInputRef = useRef<HTMLTextAreaElement>(null)

  const { conversations, currentConversationId, addConversation, addMessage, getCurrentConversation } =
    useConversationStore()

  // Default schema suggestion
  // Default schema suggestion
  const defaultSchema = `
    ### Company_name: company name,
    ### Description: brief description of the company.
    ### History: Most important milestones, aquisitions, results from last years.
    ### Business: Understand what it does, possible entry barriers or competitive advantages. Who are its suppliers and customers.
    ### Market: Who it competes with and what are its market shares.
    ### People: Board of directors, management, and shareholders, who are they? How much does the management team earn and what are their incentives based on.
    ### Capital_allocation: Analysis of M&A, money allocated to dividends, share buybacks or issuance. 
  `

  // Initialize conversation or load existing one
  useEffect(() => {
    const currentConversation = getCurrentConversation()

    // If we have a current conversation of the right type, show the chat
    if (currentConversation && currentConversation.agentType === "websearch") {
      setShowChat(true)
    } else {
      // If we don't have a current conversation or it's not the right type, don't show chat
      setShowChat(false)
    }
  }, [currentConversationId, conversations, getCurrentConversation])

  // Apply the suggested schema
  const applySuggestedSchema = () => {
    setSchema(defaultSchema)

    // Focus and scroll to the end of the textarea after setting the value
    if (schemaInputRef.current) {
      setTimeout(() => {
        const textarea = schemaInputRef.current
        if (textarea) {
          textarea.focus()
          textarea.scrollTop = textarea.scrollHeight
        }
      }, 100)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!message.trim()) return

    // Create a new conversation if needed
    let conversationId = currentConversationId
    if (!conversationId || !conversations[conversationId] || conversations[conversationId].agentType !== "websearch") {
      conversationId = addConversation("websearch")
    }

    // Prepare the full message with schema if provided
    let fullMessage = message
    if (schema) {
      fullMessage = `${message}\n\nUse the following schema for the results:\n\n${schema}\n`
    }
    const userMessage = { role: "user", content: message }
    addMessage(conversationId, userMessage)

    // Simulate agent processing
    setAgentState("searching the web")

    try {
      const schemaToSend = schema ? schema : "No schema provided, look for the required information"
      const data = await sendChatMessage_Schema(
        message,
        conversationId,
        "websearch",
        schemaToSend
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
      setShowChat(true)
    }
    /*
    setTimeout(() => {
      setAgentState("analyzing search results")

      setTimeout(() => {
        const assistantMessage = {
          role: "assistant",
          content: "Based on my web search, I found: " + message,
        }
        addMessage(conversationId, assistantMessage)
        setAgentState("idle")
      }, 1500)
    }, 1500)*/
  }

  const currentConversation = getCurrentConversation()
  const messages = currentConversation?.agentType === "websearch" ? currentConversation.messages : []

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
                <h2 className="text-2xl font-bold mb-2 flex items-center gap-2 text-green-300">
                  <Globe className="h-5 w-5" />
                  Web Search Agent
                </h2>
                <p className="mb-6 text-gray-400">
                  Ask questions and get answers based on the latest information from the web.
                </p>
              </motion.div>

              <motion.form
                onSubmit={handleSubmit}
                //className="flex gap-2"
                className="space-y-4"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3, duration: 0.5 }}
              >
                <div className="flex gap-2">
                  <Input
                    placeholder="Search the web..."
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    className="flex-1 bg-gray-700/50 border-gray-600 text-white focus:border-green-400 focus:ring-green-400/20 transition-all duration-300"
                  />
                  <Button
                    type="submit"
                    className="bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white border-0 shadow-lg shadow-green-500/20 transition-all duration-300"
                  >
                    <Search className="h-4 w-4" />
                  </Button>
                </div>
                <div className="flex items-center justify-between">
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowSchemaInput(!showSchemaInput)}
                    className="text-gray-400 hover:text-green-400 transition-colors duration-300 flex items-center gap-1"
                  >
                    {showSchemaInput ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    <span>Custom Schema {showSchemaInput ? "(Hide)" : "(Show)"}</span>
                  </Button>

                  {showSchemaInput && (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={applySuggestedSchema}
                      className="text-green-400 border-green-500/30 hover:bg-green-500/10 transition-colors duration-300 flex items-center gap-1"
                    >
                      <Lightbulb className="h-3.5 w-3.5" />
                      <span>Suggest Schema</span>
                    </Button>
                  )}
                </div>

                <AnimatePresence>
                  {showSchemaInput && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.3 }}
                    >
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <p className="text-xs text-gray-400">
                            Specify a schema to structure the search results (optional)
                          </p>
                        </div>
                        <Textarea
                          ref={schemaInputRef}
                          placeholder="Enter JSON schema for search results..."
                          value={schema}
                          onChange={(e) => setSchema(e.target.value)}
                          className="min-h-[150px] font-mono text-sm bg-gray-800/70 border-gray-600 text-white focus:border-green-400 focus:ring-green-400/20 transition-all duration-300"
                        />
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.form>
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
          <ChatInterface
            title="Web Search Agent"
            messages={messages}
            agentState={agentState}
            onSendMessage={async (newMessage) => {
              // Crear una conversación si es necesario
              let conversationId = currentConversationId;
              if (
                !conversationId ||
                !conversations[conversationId] ||
                conversations[conversationId].agentType !== "websearch"
              ) {
                conversationId = addConversation("websearch");
              }

              // Procesar el mensaje para extraer el schema si se incluye
              let userSchema = "";
              let userQuery = newMessage;
              const schemaMatch = newMessage.match(/\[SCHEMA\]\s*(\{[\s\S]*\})/);
              if (schemaMatch && schemaMatch[1]) {
                userSchema = schemaMatch[1];
                userQuery = newMessage.replace(/\[SCHEMA\]\s*(\{[\s\S]*\})/, "").trim();
              }

              // Agregar el mensaje del usuario
              addMessage(conversationId, { role: "user", content: userQuery });

              // Indicar que el agente está procesando la búsqueda
              setAgentState("searching the web");

              try {
                // Enviar schema vacío en caso de que no se haya proporcionado ninguno
                const schemaToSend = userSchema || "";
                const data = await sendChatMessage_Schema(userQuery, conversationId, "websearch", schemaToSend);
                if (data.status === "success") {
                  addMessage(conversationId, { role: "assistant", content: data.response });
                } else {
                  addMessage(conversationId, { role: "assistant", content: `Error: ${data.response || "unknown"}` });
                }
              } catch (err) {
                console.error("RAG chat error:", err);
                addMessage(conversationId, { role: "assistant", content: "😞 Sorry, something went wrong." });
              } finally {
                setAgentState("idle");
              }
            }}
            onBack={() => { 
              setShowChat(false);
              setSchema("");
            }}
            agentColor="green"
          />
        </motion.div>
      )}
    </AnimatePresence>
  )
}
