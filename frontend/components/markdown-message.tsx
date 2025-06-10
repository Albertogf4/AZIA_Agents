"use client"

import { useState } from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { motion, AnimatePresence } from "framer-motion"
import { Copy, CheckCircle2 } from "lucide-react"
import { Button } from "@/components/ui/button"

interface MarkdownMessageProps {
  content: string
  colorClasses: {
    userBubble: string
    agentBubble: string
  }
  role: string
}

export default function MarkdownMessage({ content, colorClasses, role }: MarkdownMessageProps) {
  const [isHovered, setIsHovered] = useState(false)
  const [isCopied, setIsCopied] = useState(false)

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(content)
      setIsCopied(true)
      setTimeout(() => setIsCopied(false), 2000)
    } catch (err) {
      console.error("Failed to copy text: ", err)
    }
  }

  return (
    <div
      className={`relative max-w-[80%] p-3 rounded-lg shadow-lg ${
        role === "user" ? colorClasses.userBubble : colorClasses.agentBubble
      }`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="prose prose-invert max-w-none">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]} 
          components={{
            code({ node, inline, className, children, ...props }) {
              const match = /language-(\w+)/.exec(className || "")
              return !inline ? (
                <div className="relative rounded-md overflow-hidden my-2">
                  <div className="bg-gray-900/80 px-3 py-1 text-xs text-gray-400 border-b border-gray-700">
                    {match?.[1] || "code"}
                  </div>
                  <pre className="bg-gray-900/80 p-3 overflow-x-auto border border-gray-700 rounded-b-md">
                    <code className="text-sm" {...props}>
                      {String(children).replace(/\n$/, "")}
                    </code>
                  </pre>
                </div>
              ) : (
                <code className="bg-gray-800 px-1 py-0.5 rounded text-sm" {...props}>
                  {children}
                </code>
              )
            },
            p({ children }) {
              return <p className="mb-2 last:mb-0">{children}</p>
            },
            ul({ children }) {
              return <ul className="list-disc pl-5 mb-2 space-y-1">{children}</ul>
            },
            ol({ children }) {
              return <ol className="list-decimal pl-5 mb-2 space-y-1">{children}</ol>
            },
            li({ children }) {
              return <li className="mb-1">{children}</li>
            },
            h1({ children }) {
              return <h1 className="text-xl font-bold mb-2">{children}</h1>
            },
            h2({ children }) {
              return <h2 className="text-lg font-bold mb-2">{children}</h2>
            },
            h3({ children }) {
              return <h3 className="text-md font-bold mb-2">{children}</h3>
            },
            a({ href, children }) {
              return (
                <a href={href} className="text-blue-400 hover:underline" target="_blank" rel="noopener noreferrer">
                  {children}
                </a>
              )
            },
            blockquote({ children }) {
              return (
                <blockquote className="border-l-4 border-gray-500 pl-3 italic text-gray-300 my-2">
                  {children}
                </blockquote>
              )
            },
            table({ children }) {
              return (
                <div className="overflow-x-auto my-2">
                  <table className="min-w-full divide-y divide-gray-700 border border-gray-700 rounded-md">
                    {children}
                  </table>
                </div>
              )
            },
            thead({ children }) {
              return <thead className="bg-gray-800">{children}</thead>
            },
            tbody({ children }) {
              return <tbody className="divide-y divide-gray-700">{children}</tbody>
            },
            tr({ children }) {
              return <tr>{children}</tr>
            },
            th({ children }) {
              return <th className="px-3 py-2 text-left text-xs font-medium text-gray-300 uppercase">{children}</th>
            },
            td({ children }) {
              return <td className="px-3 py-2 whitespace-nowrap text-sm">{children}</td>
            },
            hr() {
              return <hr className="my-4 border-gray-700" />
            },
          }}
        >
          {content}
        </ReactMarkdown>
      </div>

      <AnimatePresence>
        {isHovered && role === "assistant" && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ duration: 0.15 }}
            className="absolute top-2 right-2"
          >
            <Button
              size="sm"
              variant="ghost"
              className="h-8 w-8 p-0 rounded-full bg-gray-800/80 backdrop-blur-sm hover:bg-gray-700 text-gray-300"
              onClick={copyToClipboard}
              title="Copy to clipboard"
            >
              {isCopied ? <CheckCircle2 className="h-4 w-4 text-green-400" /> : <Copy className="h-4 w-4" />}
            </Button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
