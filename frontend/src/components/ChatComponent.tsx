import { FormEvent, useRef, useState } from 'react'
import { retrieveAnswer, type RetrievedChunk } from '../services/api'
import { LoadingIndicator } from './LoadingIndicator'
import { MessageBubble } from './MessageBubble'

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  sources?: RetrievedChunk[]
}

const initialMessages: ChatMessage[] = [
  {
    role: 'assistant',
    content: 'Hello! Upload some PDFs first, then ask me anything about them.',
    timestamp: 'Ready',
  },
]

export function ChatComponent() {
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages)
  const [draft, setDraft] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  function scrollToBottom() {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const trimmedDraft = draft.trim()
    if (!trimmedDraft || isLoading) return

    const userMessage: ChatMessage = {
      role: 'user',
      content: trimmedDraft,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }

    setMessages((prev) => [...prev, userMessage])
    setDraft('')
    setIsLoading(true)
    setErrorMsg(null)

    try {
      const response = await retrieveAnswer(trimmedDraft)

      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.answer,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        sources: response.results,
      }

      setMessages((prev) => [...prev, assistantMessage])
      setTimeout(scrollToBottom, 50)
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : 'Could not reach the backend. Is the server running?'
      setErrorMsg(msg)
    } finally {
      setIsLoading(false)
    }
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      event.currentTarget.form?.requestSubmit()
    }
  }

  return (
    <section className="chat-window">
      <div>
        <h2>Ask Your Documents</h2>
        <p>Questions are answered using the RAG pipeline (FAISS retrieval + Groq LLM).</p>
      </div>

      <div className="messages">
        {messages.map((message, index) => (
          <div key={`${message.role}-${index}`}>
            <MessageBubble role={message.role} content={message.content} timestamp={message.timestamp} />
            {message.sources && message.sources.length > 0 && (
              <details className="sources-panel">
                <summary>View {message.sources.length} source chunk(s)</summary>
                <ul>
                  {message.sources.map((chunk) => (
                    <li key={chunk.id}>
                      <em>Score {chunk.score.toFixed(3)} · {chunk.source_files.join(', ')}</em>
                      <p>{chunk.text}</p>
                    </li>
                  ))}
                </ul>
              </details>
            )}
          </div>
        ))}
        {isLoading ? <LoadingIndicator /> : null}
        {errorMsg && (
          <div className="result-box error-box">
            <strong>✗ Error</strong>
            <p>{errorMsg}</p>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <form className="composer" onSubmit={handleSubmit}>
        <textarea
          id="chat-input"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about your documents… (Enter to send)"
          disabled={isLoading}
        />

        <div className="composer-actions">
          <span className="chip">Connected to backend</span>
          <button id="chat-send-btn" className="primary-button" type="submit" disabled={isLoading || !draft.trim()}>
            {isLoading ? 'Thinking…' : 'Send Message'}
          </button>
        </div>
      </form>
    </section>
  )
}