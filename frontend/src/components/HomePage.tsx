import { ChatComponent } from './ChatComponent'
import { UploadComponent } from './UploadComponent'

export function HomePage() {
  return (
    <main className="shell">
      <section className="hero">
        <p className="eyebrow">RAG Document Chatbot</p>
        <h1 className="title">Upload PDFs and get grounded answers powered by Groq.</h1>
        <p className="subtitle">
          Drop your documents into the upload panel, wait for indexing, then ask anything — the assistant retrieves the
          most relevant chunks from FAISS and generates an answer with Llama 3.
        </p>
      </section>

      <section className="grid">
        <div className="panel">
          <UploadComponent />
        </div>

        <div className="panel">
          <ChatComponent />
        </div>
      </section>
    </main>
  )
}