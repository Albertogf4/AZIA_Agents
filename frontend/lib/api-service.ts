export const API_BASE_URL = "http://localhost:5328/api"

// Envio de mensajes al agente (rag y global)
export async function sendChatMessage(
  message: string,
  conversationId: string,
  agentType: "global" | "rag"
) {
  const res = await fetch(`${API_BASE_URL}/${agentType}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, conversation_id: conversationId }),
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json() as Promise<{ status: string; response: string }>
}

// Envio de mensajes al agente websearch
export async function sendChatMessage_Schema(
  message: string,
  conversationId: string,
  agentType: "websearch" | "global",
  schema: string // esquema proporciona por el usuario
) {
  const res = await fetch(`${API_BASE_URL}/${agentType}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, schema, conversation_id: conversationId }),
  })
  console.log(res)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json() as Promise<{ status: string; response: string }>
}

// Carga de archivos para el agente global y el agente rag
export async function uploadFiles(files: File[], conversationId: string, agentType: "global" | "rag" | "websearch") {
  const formData = new FormData()
  files.forEach((f) => formData.append('files', f))
  formData.append('conversation_id', conversationId)

  const res = await fetch(`${API_BASE_URL}/${agentType}/upload`, {
    method: 'POST',
    body: formData,
  })
  return res.json()
}

// Creación de vectorstore
export async function generateVectorDb(
  filePaths: { name: string; path: string; size: number }[],
  conversationId: string,
  agentType: "global" | "rag"
) {
  const res = await fetch(`${API_BASE_URL}/${agentType}/generate-vector-db`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      file_paths: filePaths,
      conversation_id: conversationId,
    }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json() as Promise<{ status: string; message?: string }>;
}