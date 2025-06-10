"use client"

import type React from "react"

import { useState, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Upload, X, FileIcon } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"

interface FileUploadProps {
  onFilesChange: (files: File[]) => void
}

export default function FileUpload({ onFilesChange }: FileUploadProps) {
  const [files, setFiles] = useState<File[]>([])
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const newFiles = Array.from(e.dataTransfer.files)
      const updatedFiles = [...files, ...newFiles]
      setFiles(updatedFiles)
      onFilesChange(updatedFiles)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const newFiles = Array.from(e.target.files)
      const updatedFiles = [...files, ...newFiles]
      setFiles(updatedFiles)
      onFilesChange(updatedFiles)
    }
  }

  const removeFile = (index: number) => {
    const updatedFiles = [...files]
    updatedFiles.splice(index, 1)
    setFiles(updatedFiles)
    onFilesChange(updatedFiles)
  }

  return (
    <div className="space-y-4">
      <Card
        className={`border-2 border-dashed p-6 text-center cursor-pointer transition-all duration-300 ${
          isDragging
            ? "border-cyan-400 bg-cyan-500/10 shadow-lg shadow-cyan-500/20"
            : "border-gray-600 bg-gray-800/50 hover:border-gray-500 hover:bg-gray-700/30"
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <motion.div
          className="flex flex-col items-center justify-center space-y-2"
          animate={{
            y: isDragging ? [0, -5, 0] : 0,
          }}
          transition={{
            repeat: isDragging ? Number.POSITIVE_INFINITY : 0,
            duration: 1.5,
          }}
        >
          <Upload
            className={`h-8 w-8 ${isDragging ? "text-cyan-400" : "text-gray-400"} transition-colors duration-300`}
          />
          <h3
            className={`text-lg font-medium ${isDragging ? "text-cyan-300" : "text-gray-300"} transition-colors duration-300`}
          >
            Drag & drop files here
          </h3>
          <p className="text-sm text-gray-500">or click to browse files</p>
        </motion.div>
        <input type="file" ref={fileInputRef} onChange={handleFileChange} className="hidden" multiple />
      </Card>

      <AnimatePresence>
        {files.length > 0 && (
          <motion.div
            className="space-y-2"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
          >
            <h4 className="text-sm font-medium text-gray-300">Uploaded Files ({files.length})</h4>
            <div className="space-y-2">
              {files.map((file, index) => (
                <motion.div
                  key={index}
                  className="flex items-center justify-between p-2 bg-gray-800/70 backdrop-blur-sm rounded-md border border-gray-700"
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 10 }}
                  transition={{ duration: 0.2, delay: index * 0.05 }}
                >
                  <div className="flex items-center space-x-2">
                    <FileIcon className="h-4 w-4 text-gray-400" />
                    <span className="text-sm truncate max-w-[200px] text-gray-300">{file.name}</span>
                    <span className="text-xs text-gray-500">({(file.size / 1024).toFixed(1)} KB)</span>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-gray-400 hover:text-white hover:bg-red-500/20"
                    onClick={(e) => {
                      e.stopPropagation()
                      removeFile(index)
                    }}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
