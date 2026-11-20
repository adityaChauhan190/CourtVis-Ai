'use client'
import { useState, useRef, useEffect, useCallback } from 'react'
import { chatApi } from '@/lib/api'
import type { ChatMessage, ChatSource, ConversationTurn } from '@/lib/types'
import styles from './CaseIntelligenceChat.module.css'

let msgCounter = 0
function newId() { return `msg-${++msgCounter}-${Date.now()}` }

// ── Quick-action categories ───────────────────────────────────────────────────

const QUICK_ACTIONS = [
  { label: 'Summarize Case', icon: '◧', query: 'Give me a comprehensive summary of this case — key facts, parties involved, and the core legal dispute.' },
  { label: 'Key Issues', icon: '⚖', query: 'What are the key legal issues I need to focus on in this case?' },
  { label: 'Weaknesses', icon: '◈', query: 'What are the weaknesses in this case? Structure your response with each weakness, supporting evidence, why it matters, and recommended action.' },
  { label: 'Arguments', icon: '§', query: 'What are the strongest legal arguments available? Provide a structured analysis with supporting evidence from the documents.' },
  { label: 'Timeline', icon: '◎', query: 'List all important dates and events in this case in chronological order.' },
  { label: 'Parties', icon: '⊕', query: 'Identify all parties involved in this case and their roles.' },
  { label: 'Evidence', icon: '◪', query: 'What evidence is present in these documents? List and categorize it.' },
  { label: 'Missing Docs', icon: '⊞', query: 'What documents or evidence appear to be missing from this case file that I should obtain?' },
  { label: 'Hearing Prep', icon: '◫', query: 'Give me a hearing preparation checklist based on the case documents.' },
  { label: 'Opposing Side', icon: '⟳', query: 'Prepare questions for the opposing party based on the case documents.' },
]

function formatTime(date: Date) {
  return date.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
}

// ── localStorage helpers ─────────────────────────────────────────────────────

interface SerializedMessage {
  id: string
  role: string
  content: string
  sources?: ChatSource[]
  model?: string
  timestamp: string
  isError?: boolean
}

function saveHistory(caseId: string, messages: ChatMessage[]) {
  try {
    const serialized: SerializedMessage[] = messages
      .filter(m => !m.isLoading)
      .map(m => ({
        id: m.id,
        role: m.role,
        content: m.content,
        sources: m.sources,
        model: m.model,
        timestamp: m.timestamp.toISOString(),
        isError: m.isError,
      }))
    localStorage.setItem(`chat_history_${caseId}`, JSON.stringify(serialized))
  } catch { /* storage full or unavailable */ }
}

function loadHistory(caseId: string): ChatMessage[] {
  try {
    const raw = localStorage.getItem(`chat_history_${caseId}`)
    if (!raw) return []
    const parsed: SerializedMessage[] = JSON.parse(raw)
    return parsed.map(m => ({
      id: m.id,
      role: m.role as 'user' | 'assistant',
      content: m.content,
      sources: m.sources,
      model: m.model,
      timestamp: new Date(m.timestamp),
      isError: m.isError,
    }))
  } catch { return [] }
}

function clearHistory(caseId: string) {
  try { localStorage.removeItem(`chat_history_${caseId}`) } catch { /* noop */ }
}

// ── Component Props ──────────────────────────────────────────────────────────

interface Props {
  caseId: string
  documentCount: number
  caseName?: string
}

export function CaseIntelligenceChat({ caseId, documentCount, caseName }: Props) {
  const hasDocuments = documentCount > 0

  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showActions, setShowActions] = useState(true)
  const [hydrated, setHydrated] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // ── Rehydrate from localStorage on mount ───────────────────────────────────
  useEffect(() => {
    const saved = loadHistory(caseId)
    if (saved.length > 0) {
      setMessages(saved)
      setShowActions(false)
    }
    setHydrated(true)
  }, [caseId])

  // ── Auto-scroll to newest message ──────────────────────────────────────────
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // ── Hide quick actions once conversation starts ────────────────────────────
  useEffect(() => {
    if (messages.length > 0) setShowActions(false)
  }, [messages.length])

  // ── Persist to localStorage whenever messages change ──────────────────────
  useEffect(() => {
    if (!hydrated) return
    saveHistory(caseId, messages)
  }, [messages, caseId, hydrated])

  /** Build conversation history array from current messages for backend context */
  function buildHistory(currentMessages: ChatMessage[]): ConversationTurn[] {
    return currentMessages
      .filter(m => !m.isLoading && !m.isError && m.content)
      .map(m => ({ role: m.role, content: m.content }))
  }

  const sendMessage = useCallback(async (text: string) => {
    const userText = text.trim()
    if (!userText || isLoading) return

    const userMsg: ChatMessage = {
      id: newId(),
      role: 'user',
      content: userText,
      timestamp: new Date(),
    }
    const loadingMsgId = newId()
    const loadingMsg: ChatMessage = {
      id: loadingMsgId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isLoading: true,
    }

    // Capture history from current messages BEFORE adding the new user message.
    // The backend receives `conversation_history` (prior turns) + the new message separately.
    const historySnapshot = buildHistory(messages)

    setMessages(prev => [...prev, userMsg, loadingMsg])
    setInput('')
    setIsLoading(true)

    try {
      // ── Streaming path ─────────────────────────────────────────────────────
      let streamedContent = ''
      let finalSources: ChatSource[] = []
      let finalModel = ''

      const stream = chatApi.sendMessageStream(caseId, userText, historySnapshot)

      for await (const event of stream) {
        if (event.type === 'token' && event.content) {
          streamedContent += event.content
          // Update the bubble with accumulated text in real-time
          setMessages(curr =>
            curr.map(m =>
              m.id === loadingMsgId
                ? { ...m, content: streamedContent, isLoading: false }
                : m
            )
          )
        } else if (event.type === 'done') {
          finalSources = (event.sources as ChatSource[]) ?? []
          finalModel = event.model ?? ''
          // Apply final state with sources + model
          setMessages(curr =>
            curr.map(m =>
              m.id === loadingMsgId
                ? {
                    ...m,
                    content: streamedContent || event.answer || '',
                    sources: finalSources,
                    model: finalModel,
                    isLoading: false,
                  }
                : m
            )
          )
        } else if (event.type === 'error') {
          throw new Error(event.message ?? 'Streaming error')
        }
      }
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : 'An error occurred.'
      setMessages(curr =>
        curr.map(m =>
          m.id === loadingMsgId
            ? { ...m, content: errMsg, isLoading: false, isError: true }
            : m
        )
      )
    } finally {
      setIsLoading(false)
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }, [caseId, isLoading, messages])


  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
  }

  function handleNewChat() {
    setMessages([])
    setShowActions(true)
    clearHistory(caseId)
  }

  const isConversationEmpty = messages.length === 0

  return (
    <div className={styles.chat}>
      {/* ── Header ────────────────────────────────────────── */}
      <div className={styles.chatHeader}>
        <div className={styles.chatHeaderLeft}>
          <div className={styles.aiIcon}>◈</div>
          <div>
            <p className={styles.chatTitle}>Case Intelligence</p>
            <p className={styles.chatSubtitle}>
              Powered by Groq · llama-3.3-70b-versatile
              <span className={`${styles.statusDot} ${hasDocuments ? styles.statusDotReady : styles.statusDotIdle}`} />
              {hasDocuments ? `${documentCount} doc${documentCount > 1 ? 's' : ''} indexed` : 'Awaiting docs'}
            </p>
          </div>
        </div>
        <div className={styles.chatHeaderRight}>
          {messages.length > 0 && (
            <button
              className={styles.resetBtn}
              onClick={handleNewChat}
              title="Start new conversation"
            >
              New Chat
            </button>
          )}
          <span className={`badge ${hasDocuments ? 'badge-ready' : 'badge-coming-soon'}`}>
            {hasDocuments ? 'Ready' : 'No docs'}
          </span>
        </div>
      </div>

      {/* ── Messages ──────────────────────────────────────── */}
      <div className={styles.messages} id="chat-messages-container">
        {/* Empty state — shown when no messages yet */}
        {isConversationEmpty && (
          <div className={styles.emptyState}>
            <div className={styles.emptyIcon}>◈</div>
            {hasDocuments ? (
              <>
                <h3 className={`${styles.emptyTitle} font-display`}>
                  Your case has been analysed.
                </h3>
                <p className={styles.emptySubtitle}>
                  {caseName
                    ? `Ready to investigate ${caseName}.`
                    : 'Ready to investigate your case.'}
                  {' '}Choose an action below, or ask anything.
                </p>
                <div className={styles.emptyActions}>
                  {[
                    { label: 'Understand the Case', query: 'Give me a comprehensive summary of this case — key facts, parties involved, and the core legal dispute.' },
                    { label: 'Find Weaknesses', query: 'What are the weaknesses in this case? Structure your response with each weakness, supporting evidence, why it matters, and recommended action.' },
                    { label: 'Analyse Evidence', query: 'What evidence is present in these documents? List and categorize it.' },
                    { label: 'Build Timeline', query: 'List all important dates and events in this case in chronological order.' },
                    { label: 'Prepare Arguments', query: 'What are the strongest legal arguments available? Provide a structured analysis with supporting evidence from the documents.' },
                    { label: 'Hearing Prep', query: 'Give me a hearing preparation checklist based on the case documents.' },
                  ].map((a, i) => (
                    <button
                      key={i}
                      id={`empty-action-${i}`}
                      className={styles.emptyActionBtn}
                      onClick={() => sendMessage(a.query)}
                      disabled={isLoading}
                    >
                      {a.label}
                    </button>
                  ))}
                </div>
              </>
            ) : (
              <>
                <h3 className={`${styles.emptyTitle} font-display`}>
                  Upload documents to begin.
                </h3>
                <p className={styles.emptySubtitle}>
                  Add case documents using the panel on the left. Once processed, you can ask questions about the case.
                </p>
              </>
            )}
          </div>
        )}

        {messages.map(msg => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        <div ref={bottomRef} />
      </div>

      {/* ── Quick Actions Bar ────────────────────────────── */}
      {hasDocuments && showActions && !isConversationEmpty && (
        <div className={styles.quickActions} id="quick-actions-bar">
          <p className={styles.quickActionsLabel}>Quick actions</p>
          <div className={styles.quickActionsScroll}>
            {QUICK_ACTIONS.map((a, i) => (
              <button
                key={i}
                id={`quick-action-${i}`}
                className={styles.quickActionChip}
                onClick={() => sendMessage(a.query)}
                disabled={isLoading}
                title={a.query}
              >
                <span className={styles.chipIcon}>{a.icon}</span>
                {a.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ── Input ─────────────────────────────────────────── */}
      <div className={styles.inputArea}>
        <div className={styles.inputWrapper}>
          <textarea
            ref={inputRef}
            id="chat-input"
            className={styles.input}
            placeholder={
              hasDocuments
                ? 'Ask anything about the case… (Enter to send, Shift+Enter for new line)'
                : 'Upload case documents first to enable AI analysis…'
            }
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
            disabled={isLoading || !hasDocuments}
          />
          <button
            id="chat-send-btn"
            className={styles.sendBtn}
            onClick={() => sendMessage(input)}
            disabled={isLoading || !input.trim() || !hasDocuments}
            aria-label="Send message"
          >
            {isLoading ? <span className="spinner" /> : <SendIcon />}
          </button>
        </div>
        <p className={styles.inputDisclaimer}>
          AI answers are grounded in uploaded documents. Always verify with primary sources.
          {messages.length > 0 && (
            <span style={{ marginLeft: 8, opacity: 0.5, fontSize: '0.7rem' }}>
              · History saved locally
            </span>
          )}
        </p>
      </div>
    </div>
  )
}

// ── Message Bubble ────────────────────────────────────────────────────────────

function MessageBubble({ message: msg }: { message: ChatMessage }) {
  const isUser = msg.role === 'user'

  return (
    <div className={`${styles.messageRow} ${isUser ? styles.messageRowUser : styles.messageRowAi}`}>
      {!isUser && (
        <div className={styles.avatar} aria-hidden="true">◈</div>
      )}
      <div className={`${styles.bubble} ${isUser ? styles.bubbleUser : styles.bubbleAi} ${msg.isError ? styles.bubbleError : ''}`}>
        {msg.isLoading ? (
          <TypingIndicator />
        ) : (
          <>
            <div
              className={styles.bubbleContent}
              dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.content) }}
            />
            {msg.sources && msg.sources.length > 0 && (
              <SourceCitations sources={msg.sources} />
            )}
            <div className={styles.bubbleMeta}>
              <span className={styles.bubbleTime}>{formatTime(msg.timestamp)}</span>
              {msg.model && msg.model !== 'none' && (
                <span className={styles.bubbleModel}>{msg.model}</span>
              )}
            </div>
          </>
        )}
      </div>
      {isUser && (
        <div className={`${styles.avatar} ${styles.avatarUser}`} aria-hidden="true">⚖</div>
      )}
    </div>
  )
}

// ── Source Citations ──────────────────────────────────────────────────────────

function SourceCitations({ sources }: { sources: ChatSource[] }) {
  const [expanded, setExpanded] = useState(false)

  if (sources.length === 0) return null

  return (
    <div className={styles.sources}>
      <button
        className={styles.sourcesToggle}
        onClick={() => setExpanded(v => !v)}
        aria-expanded={expanded}
      >
        <span className={styles.sourcesIcon}>◧</span>
        {sources.length} source{sources.length > 1 ? 's' : ''}
        <span className={styles.sourcesChevron}>{expanded ? '▲' : '▼'}</span>
      </button>

      {expanded && (
        <div className={styles.sourceList}>
          {sources.map((s, i) => (
            <div key={i} className={styles.sourceItem}>
              <div className={styles.sourceHeader}>
                <span className={styles.sourceDocName}>{s.document_name}</span>
                {s.page_hint && (
                  <span className={styles.sourcePages}>{s.page_hint}</span>
                )}
              </div>
              <p className={styles.sourceExcerpt}>"{s.excerpt}"</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ── Typing Indicator ─────────────────────────────────────────────────────────

function TypingIndicator() {
  return (
    <div className={styles.typing} aria-label="AI is thinking">
      <span className={styles.typingDot} />
      <span className={styles.typingDot} />
      <span className={styles.typingDot} />
      <span className={styles.typingLabel}>Analysing documents…</span>
    </div>
  )
}

// ── Send Icon ─────────────────────────────────────────────────────────────────

function SendIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  )
}

// ── Markdown renderer (minimal, safe) ─────────────────────────────────────────

function renderMarkdown(text: string): string {
  const processed = text
    // Bold **text**
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    // Italic *text*
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // Inline code `code`
    .replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
    // Headings ## text
    .replace(/^## (.+)$/gm, '<h3 class="md-h3">$1</h3>')
    .replace(/^### (.+)$/gm, '<h4 class="md-h4">$1</h4>')
    // Bullet lists
    .replace(/^[-•–] (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>(\n|$))+/g, '<ul class="md-ul">$&</ul>')
    // Numbered lists
    .replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
    // Line breaks
    .replace(/\n\n/g, '</p><p class="md-p">')
    .replace(/\n/g, '<br/>')
  // Wrap in paragraph (avoid dotAll flag for TS compat)
  const wrapped = processed.startsWith('<') ? processed : '<p class="md-p">' + processed
  return wrapped.endsWith('>') ? wrapped : wrapped + '</p>'
}
