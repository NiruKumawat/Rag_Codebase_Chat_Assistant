import axios from 'axios'

// ── Axios client ──────────────────────────────────────────────────────────────
// In dev, Vite proxies /api → http://localhost:8000 so no CORS issues.
// In prod, set VITE_API_BASE_URL to your deployed backend origin.
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '',
  timeout: 300_000, // 5 min — the first upload downloads the embedding model (~90 MB)
})

// ── Types ─────────────────────────────────────────────────────────────────────

export interface FaissWriteResult {
  added: number
  total_vectors: number
  index_path: string
  metadata_path: string
}

export interface UploadResponse {
  message: string
  files: string[]
  count: number
  chunks: string[]
  faiss: FaissWriteResult
}

export interface RetrievedChunk {
  id: number
  score: number
  chunk_index: number
  source_files: string[]
  text: string
}

export interface RetrievalResponse {
  question: string
  top_k: number
  results: RetrievedChunk[]
  answer: string
}

// ── API calls ─────────────────────────────────────────────────────────────────

/** Upload one or more PDF files for ingestion into FAISS.
 *  The first call may take a while — sentence-transformers downloads the
 *  embedding model on first use. We use a 5-minute timeout to cover that.
 */
export async function uploadPDFs(
  files: File[],
  onProgress?: (pct: number) => void,
): Promise<UploadResponse> {
  const form = new FormData()
  for (const file of files) {
    form.append('files', file, file.name)
  }
  const { data } = await apiClient.post<UploadResponse>('/api/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 300_000, // 5 min
    onUploadProgress: (event) => {
      if (onProgress && event.total) {
        onProgress(Math.round((event.loaded / event.total) * 100))
      }
    },
  })
  return data
}

/** Send a question and receive a grounded answer from the RAG pipeline. */
export async function retrieveAnswer(question: string): Promise<RetrievalResponse> {
  const { data } = await apiClient.post<RetrievalResponse>('/api/retrieve', { question })
  return data
}