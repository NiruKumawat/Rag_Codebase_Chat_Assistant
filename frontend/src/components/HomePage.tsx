import { FormEvent, useRef, useState } from 'react'
import { retrieveAnswer, uploadPDFs, type RetrievedChunk, type UploadResponse } from '../services/api'

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: RetrievedChunk[]
}

const initialMessages: ChatMessage[] = [
  {
    id: 'welcome-msg',
    role: 'assistant',
    content: "Hello! I'm your RAG chatbot. Upload a PDF document and ask me questions about it!",
  },
]

export function HomePage() {
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages)
  const [draft, setDraft] = useState('')
  const [isAsking, setIsAsking] = useState(false)
  const [showUpload, setShowUpload] = useState(true)

  // Upload states
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [selectedFileNames, setSelectedFileNames] = useState<string[]>([])

  const fileInputRef = useRef<HTMLInputElement>(null)
  const chatEndRef = useRef<HTMLDivElement>(null)

  function scrollToBottom() {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  function handleNewChat() {
    setMessages(initialMessages)
    setDraft('')
  }

  function handleToggleUpload() {
    setShowUpload((prev) => !prev)
  }

  function triggerFilePicker() {
    fileInputRef.current?.click()
  }

  async function handleFilesSelected(event: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files ?? [])
    if (files.length === 0) return

    setSelectedFileNames(files.map((f) => f.name))
    setIsUploading(true)
    setUploadProgress(0)
    setUploadError(null)
    setUploadResult(null)

    try {
      const response = await uploadPDFs(files, setUploadProgress)
      setUploadResult(response)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Upload failed. Ensure the backend is running.'
      setUploadError(msg)
    } finally {
      setIsUploading(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  async function handleSendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const trimmed = draft.trim()
    if (!trimmed || isAsking) return

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: trimmed,
    }

    setMessages((prev) => [...prev, userMessage])
    setDraft('')
    setIsAsking(true)
    setTimeout(scrollToBottom, 50)

    try {
      const response = await retrieveAnswer(trimmed)
      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.answer,
        sources: response.results,
      }
      setMessages((prev) => [...prev, assistantMessage])
    } catch (err: any) {
      const msg = err?.response?.data?.detail || (err instanceof Error ? err.message : 'Could not reach backend server.')
      const errorMessage: ChatMessage = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: `⚠️ ${msg}`,
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsAsking(false)
      setTimeout(scrollToBottom, 50)
    }
  }

  return (
    <div className="app-container">
      {/* ── Top Header ────────────────────────────────────────── */}
      <header className="app-header">
        <div className="header-brand">
          <h1 className="header-title">RAG Chatbot</h1>
        </div>

        <div className="header-actions">
          <button className="btn-outline" type="button" onClick={handleNewChat}>
            New chat
          </button>
          <button
            className={`btn-outline ${showUpload ? 'active' : ''}`}
            type="button"
            onClick={handleToggleUpload}
          >
            Upload PDF
          </button>
        </div>
      </header>

      {/* ── Main Scrollable Content ────────────────────────────── */}
      <main className="main-content">
        {/* ── Upload Card ──────────────────────────────────────── */}
        {showUpload && (
          <section className="upload-card">
            <div className="upload-card-header">
              <span className="upload-icon">📄</span>
              <span>Upload PDF Document</span>
            </div>

            <input
              ref={fileInputRef}
              type="file"
              accept="application/pdf,.pdf"
              multiple
              style={{ display: 'none' }}
              onChange={handleFilesSelected}
              disabled={isUploading}
            />

            <button
              className="btn-choose-file"
              type="button"
              onClick={triggerFilePicker}
              disabled={isUploading}
            >
              {isUploading ? 'Uploading & Indexing…' : 'Choose PDF File'}
            </button>

            {isUploading && (
              <div className="upload-info-box">
                <div>Uploading {selectedFileNames.join(', ')} ({uploadProgress}%)…</div>
                <div className="progress-bar-container">
                  <div className="progress-bar-fill" style={{ width: `${uploadProgress}%` }} />
                </div>
              </div>
            )}

            {uploadResult && (
              <div className="upload-info-box success">
                📄 <strong>{(uploadResult.files?.length ? uploadResult.files : selectedFileNames).join(', ')}</strong> ({uploadResult.faiss.added} chunks indexed successfully)
              </div>
            )}

            {uploadError && (
              <div className="upload-info-box error">
                ✗ {uploadError}
              </div>
            )}
          </section>
        )}

        {/* ── Chat Messages Thread ─────────────────────────────── */}
        <section className="chat-thread">
          {messages.map((msg) => (
            <div key={msg.id} className={`message-item ${msg.role}`}>
              <div className={`chat-bubble ${msg.role}`}>
                <div>{msg.content}</div>
              </div>
            </div>
          ))}

          {isAsking && (
            <div className="message-item assistant">
              <div className="typing-indicator" aria-label="Thinking">
                <span className="typing-dot" />
                <span className="typing-dot" />
                <span className="typing-dot" />
              </div>
            </div>
          )}

          <div ref={chatEndRef} />
        </section>
      </main>

      {/* ── Bottom Fixed Input ─────────────────────────────────── */}
      <footer className="input-footer">
        <form className="chat-form" onSubmit={handleSendMessage}>
          <input
            className="chat-input"
            type="text"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="Ask something..."
            disabled={isAsking}
          />
          <button className="btn-submit" type="submit" disabled={isAsking || !draft.trim()}>
            Submit
          </button>
        </form>
      </footer>
    </div>
  )
}