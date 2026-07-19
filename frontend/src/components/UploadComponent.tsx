import { useMemo, useRef, useState } from 'react'
import { uploadPDFs, type UploadResponse } from '../services/api'

type FileStatus = 'queued' | 'uploading' | 'success' | 'error'

interface FileEntry {
  file: File
  status: FileStatus
}

export function UploadComponent() {
  const [entries, setEntries] = useState<FileEntry[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [result, setResult] = useState<UploadResponse | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const totalSizeMb = useMemo(() => {
    const bytes = entries.reduce((sum, e) => sum + e.file.size, 0)
    return (bytes / (1024 * 1024)).toFixed(2)
  }, [entries])

  function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files ?? [])
    setEntries(files.map((file) => ({ file, status: 'queued' })))
    setResult(null)
    setErrorMsg(null)
  }

  async function handleUpload() {
    if (entries.length === 0 || isUploading) return

    setIsUploading(true)
    setUploadProgress(0)
    setErrorMsg(null)
    setResult(null)
    setEntries((prev) => prev.map((e) => ({ ...e, status: 'uploading' })))

    try {
      const files = entries.map((e) => e.file)
      const response = await uploadPDFs(files, setUploadProgress)
      setEntries((prev) => prev.map((e) => ({ ...e, status: 'success' })))
      setResult(response)
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : 'Upload failed. Make sure the backend is running.'
      setErrorMsg(msg)
      setEntries((prev) => prev.map((e) => ({ ...e, status: 'error' })))
    } finally {
      setIsUploading(false)
    }
  }

  function handleReset() {
    setEntries([])
    setResult(null)
    setErrorMsg(null)
    if (inputRef.current) inputRef.current.value = ''
  }

  const statusLabel: Record<FileStatus, string> = {
    queued: 'Queued',
    uploading: 'Uploading…',
    success: 'Indexed ✓',
    error: 'Failed ✗',
  }

  return (
    <section>
      <h2>Upload PDF Files</h2>
      <p>Select one or more PDFs to ingest into the vector store.</p>

      <div className="upload-dropzone">
        <strong>PDF intake area</strong>
        <input
          ref={inputRef}
          id="pdf-file-input"
          type="file"
          accept="application/pdf,.pdf"
          multiple
          onChange={handleFileChange}
          disabled={isUploading}
        />
        <span className="chip">{entries.length} file(s) selected</span>
      </div>

      <ul className="file-list">
        {entries.length === 0 ? (
          <li className="file-card">
            <div>
              <strong>No files chosen yet</strong>
              <div>
                <span>Choose PDF files above, then click Upload.</span>
              </div>
            </div>
            <span className="status-pill">Ready</span>
          </li>
        ) : (
          entries.map(({ file, status }) => (
            <li key={`${file.name}-${file.size}`} className="file-card">
              <div>
                <strong>{file.name}</strong>
                <div>
                  <span>{(file.size / 1024).toFixed(1)} KB · PDF</span>
                </div>
              </div>
              <span
                className={`status-pill ${status === 'success' ? 'success' : status === 'error' ? 'error' : ''}`}
              >
                {statusLabel[status]}
              </span>
            </li>
          ))
        )}
      </ul>

      <div className="section-gap" />
      <p>
        Total size: <strong>{totalSizeMb} MB</strong>
      </p>

      <div className="composer-actions">
        {result ? (
          <button className="primary-button" type="button" onClick={handleReset}>
            Upload More
          </button>
        ) : (
          <button
            id="upload-submit-btn"
            className="primary-button"
            type="button"
            onClick={handleUpload}
            disabled={entries.length === 0 || isUploading}
          >
            {isUploading ? 'Uploading…' : 'Upload & Index'}
          </button>
        )}
      </div>

      {isUploading && (
        <div className="result-box" style={{ background: 'rgba(115,201,255,0.08)', border: '1px solid rgba(115,201,255,0.25)', color: 'var(--accent)' }}>
          <strong>⏳ {uploadProgress < 100 ? `Uploading… ${uploadProgress}%` : 'Indexing — downloading embedding model on first run…'}</strong>
          <p>The first upload downloads the AI embedding model (~90 MB). This takes 1–2 minutes once, then it's cached.</p>
          <div style={{ marginTop: 10, height: 6, borderRadius: 99, background: 'rgba(255,255,255,0.08)' }}>
            <div style={{ width: `${uploadProgress}%`, height: '100%', borderRadius: 99, background: 'var(--accent)', transition: 'width 0.3s ease' }} />
          </div>
        </div>
      )}

      {result && (
        <div className="result-box success-box">
          <strong>✓ {result.message}</strong>
          <p>
            {result.count} file(s) → {result.chunks.length} chunks → {result.faiss.added} vectors added (
            {result.faiss.total_vectors} total in FAISS).
          </p>
        </div>
      )}

      {errorMsg && (
        <div className="result-box error-box">
          <strong>✗ Upload error</strong>
          <p>{errorMsg}</p>
        </div>
      )}
    </section>
  )
}