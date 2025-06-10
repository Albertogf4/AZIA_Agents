import { create } from "zustand"
import { persist } from "zustand/middleware"

export interface Message {
  role: string
  content: string
}

// Update the Conversation interface to include file information
export interface Conversation {
  title: string
  agentType: "global" | "rag" | "websearch"
  messages: Message[]
  timestamp: number
  files?: {
    count: number
    names: string[]
    totalSize: number
  }
}

// Update the example conversations to include file information and Markdown content
const exampleConversations: Record<string, Conversation> = {
  "conv-1": {
    title: "Climate change impacts",
    agentType: "global",
    messages: [
      { role: "user", content: "What are the main impacts of climate change?" },
      {
        role: "assistant",
        content: `# Climate Change Impacts

Climate change leads to several major impacts globally:

1. **Rising temperatures** - Global warming is causing average temperatures to increase worldwide
2. **Sea level rise** - Melting ice caps and thermal expansion are raising sea levels
3. **Extreme weather events** - More frequent and intense storms, floods, and droughts
4. **Ecosystem disruption** - Changes in habitats affecting plant and animal species

These changes affect:
- Agriculture and food security
- Water resources and availability
- Human health and disease patterns
- Biodiversity and ecosystem services

## Regional Variations

Different regions experience climate change impacts differently:

| Region | Primary Impacts |
|--------|----------------|
| Arctic | Rapid ice loss, permafrost thawing |
| Coastal | Flooding, erosion, saltwater intrusion |
| Tropical | Changing rainfall patterns, extreme heat |
| Arid | Increased drought, water scarcity |

\`\`\`python
# Simple model of temperature increase
def temp_increase(baseline, years, rate=0.03):
    return baseline + (years * rate)
\`\`\`

> "Climate change is the defining crisis of our time and it is happening even more quickly than we feared." - UN`,
      },
    ],
    timestamp: Date.now() - 1000 * 60 * 60 * 2, // 2 hours ago
    files: {
      count: 2,
      names: ["climate_report.pdf", "global_warming_data.csv"],
      totalSize: 3500000,
    },
  },
  "conv-2": {
    title: "Machine learning basics",
    agentType: "rag",
    messages: [
      { role: "user", content: "Explain the difference between supervised and unsupervised learning" },
      {
        role: "assistant",
        content: `# Supervised vs Unsupervised Learning

Based on your documents, here's a comparison:

## Supervised Learning

Supervised learning uses **labeled data** to train models that can make predictions. The algorithm learns from input-output pairs.

### Key characteristics:
- Requires labeled training data
- Has a clear target variable
- Focuses on prediction
- Performance can be measured precisely

### Common algorithms:
- Linear Regression
- Logistic Regression
- Support Vector Machines (SVM)
- Decision Trees and Random Forests
- Neural Networks

\`\`\`javascript
// Simple supervised learning example
function predictPrice(squareFeet, bedrooms, neighborhood) {
  return (squareFeet * 150) + (bedrooms * 20000) + neighborhoodFactor(neighborhood);
}
\`\`\`

## Unsupervised Learning

Unsupervised learning identifies **patterns in unlabeled data** without specific guidance.

### Key characteristics:
- Works with unlabeled data
- No target variable
- Focuses on finding structure or relationships
- Performance is harder to measure

### Common algorithms:
- K-means Clustering
- Hierarchical Clustering
- Principal Component Analysis (PCA)
- Association Rules
- Autoencoders

![Comparison diagram](https://example.com/ml_comparison.png)

> Note: Semi-supervised learning combines both approaches by using a small amount of labeled data with a large amount of unlabeled data.`,
      },
    ],
    timestamp: Date.now() - 1000 * 60 * 60 * 24, // 1 day ago
    files: {
      count: 3,
      names: ["ml_textbook.pdf", "algorithms.docx", "training_data.xlsx"],
      totalSize: 8200000,
    },
  },
  "conv-3": {
    title: "Latest tech news",
    agentType: "websearch",
    messages: [
      { role: "user", content: "What are the latest developments in quantum computing?" },
      {
        role: "assistant",
        content: `# Recent Quantum Computing Developments

Based on my web search, here are the latest breakthroughs in quantum computing:

## Error Correction Advances
Researchers have made significant progress in quantum error correction, which is crucial for building practical quantum computers:

- **Surface code improvements** - New techniques have reduced the overhead required for error correction
- **Logical qubit demonstrations** - Several labs have demonstrated logical qubits with error rates below the threshold for fault tolerance

## Hardware Improvements
New quantum processors are showing impressive capabilities:

1. **Increased qubit counts** - Several companies have announced processors with 100+ qubits
2. **Reduced error rates** - Improved coherence times and gate fidelities
3. **New qubit types** - Advances in different qubit technologies:
   - Superconducting circuits
   - Trapped ions
   - Silicon spin qubits
   - Photonic systems

## Algorithmic Breakthroughs
New quantum algorithms are showing promise for practical applications:

\`\`\`
Quantum Advantage Domains:
- Chemistry simulation
- Optimization problems
- Machine learning
- Cryptography
\`\`\`

## Industry Adoption
Major companies are investing heavily in quantum technology:

| Company | Focus Area | Recent Announcement |
|---------|------------|---------------------|
| IBM | Hardware/Software | 1000+ qubit roadmap |
| Google | Error correction | Logical qubit milestone |
| Microsoft | Topological qubits | Azure Quantum expansion |
| Amazon | Cloud access | Bracket service updates |

These developments suggest quantum computing is moving steadily from research to practical applications, though significant challenges remain.`,
      },
    ],
    timestamp: Date.now() - 1000 * 60 * 60 * 24 * 3, // 3 days ago
  },
}

interface ConversationStore {
  conversations: Record<string, Conversation>
  currentConversationId: string | null
  addConversation: (agentType: "global" | "rag" | "websearch") => string
  updateConversation: (id: string, conversation: Partial<Conversation>) => void
  addMessage: (id: string, message: Message) => void
  setCurrentConversationId: (id: string | null) => void
  getCurrentConversation: () => Conversation | null
  updateConversationFiles: (id: string, files: any) => void
}

// Add updateConversationFiles method to the store
export const useConversationStore = create<ConversationStore>()(
  persist(
    (set, get) => ({
      conversations: exampleConversations,
      currentConversationId: null,

      addConversation: (agentType) => {
        const id = `conv-${Date.now()}`
        const defaultTitle =
          agentType === "global" ? "New conversation" : agentType === "rag" ? "Document analysis" : "Web search"

        set((state) => ({
          conversations: {
            ...state.conversations,
            [id]: {
              title: defaultTitle,
              agentType,
              messages: [],
              timestamp: Date.now(),
            },
          },
          currentConversationId: id,
        }))

        return id
      },

      updateConversation: (id, conversation) => {
        set((state) => ({
          conversations: {
            ...state.conversations,
            [id]: {
              ...state.conversations[id],
              ...conversation,
              timestamp: Date.now(),
            },
          },
        }))
      },

      updateConversationFiles: (id, files) => {
        set((state) => {
          const conversation = state.conversations[id]
          if (!conversation) return state

          return {
            conversations: {
              ...state.conversations,
              [id]: {
                ...conversation,
                files,
                timestamp: Date.now(),
              },
            },
          }
        })
      },

      addMessage: (id, message) => {
        set((state) => {
          const conversation = state.conversations[id]
          if (!conversation) return state

          // Update title based on first user message if it's still the default
          let title = conversation.title
          if (
            message.role === "user" &&
            conversation.messages.length === 0 &&
            (title === "New conversation" || title === "Document analysis" || title === "Web search")
          ) {
            // Use the first 30 chars of the message as the title
            title = message.content.length > 30 ? `${message.content.substring(0, 30)}...` : message.content
          }

          return {
            conversations: {
              ...state.conversations,
              [id]: {
                ...conversation,
                title,
                messages: [...conversation.messages, message],
                timestamp: Date.now(),
              },
            },
          }
        })
      },

      setCurrentConversationId: (id) => {
        set({ currentConversationId: id })
      },

      getCurrentConversation: () => {
        const { conversations, currentConversationId } = get()
        return currentConversationId ? conversations[currentConversationId] : null
      },
    }),
    {
      name: "conversation-storage",
    },
  ),
)
