type MessageRole = 'user' | 'assistant'

interface MessageBubbleProps {
  role: MessageRole
  content: string
  timestamp: string
}

export function MessageBubble({ role, content, timestamp }: MessageBubbleProps) {
  return (
    <div className={`message-row ${role}`}>
      <div className={`bubble ${role}`}>
        {content}
        <div className="bubble-meta">{role === 'user' ? 'You' : 'Assistant'} · {timestamp}</div>
      </div>
    </div>
  )
}