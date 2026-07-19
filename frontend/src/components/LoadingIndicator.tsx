export function LoadingIndicator() {
  return (
    <div className="loading" aria-live="polite" aria-label="Loading response">
      <span>Generating a response preview</span>
      <span className="dots" aria-hidden="true">
        <span />
        <span />
        <span />
      </span>
    </div>
  )
}