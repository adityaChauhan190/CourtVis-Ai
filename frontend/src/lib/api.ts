/**
 * Court Vision AI — API Client Service Layer
 *
 * Centralised API access. All components use this module —
 * never raw fetch() calls — so the base URL and auth headers
 * are managed in one place.
 */

import type {
  Case,
  CaseCreate,
  CaseListResponse,
  Document,
  DocumentListResponse,
  DocumentStatus_,
  ChatResponse,
  CaseSummaryResponse,
  ConversationTurn,
  GraphResponse,
  SessionTurn,
  CourtroomResponse,
  VerdictResponse,
  JudgeTemperament,
  TrialBriefResponse,
  ResearchResponse,
} from '@/lib/types'


const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public detail?: unknown,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${API_BASE}${path}`
  
  // Retrieve token dynamically
  let token = null
  if (typeof window !== 'undefined') {
    token = localStorage.getItem('access_token')
  }

  const res = await fetch(url, {
    ...options,
    headers: {
      ...(options.headers ?? {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  })

  if (!res.ok) {
    let detail: unknown
    try {
      detail = await res.json()
    } catch {
      detail = await res.text()
    }
    const message =
      typeof detail === 'object' && detail !== null && 'detail' in detail
        ? String((detail as { detail: unknown }).detail)
        : `Request failed with status ${res.status}`

    // If the server says our token is invalid, clear it and force re-login
    if (res.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('access_token')
      if (window.location.pathname !== '/auth') {
        window.location.href = '/auth'
      }
    }

    throw new ApiError(res.status, message, detail)
  }

  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

// ── Cases ─────────────────────────────────────────────────────────────────────

export const casesApi = {
  list(): Promise<CaseListResponse> {
    return request<CaseListResponse>('/api/cases')
  },

  get(id: string): Promise<Case> {
    return request<Case>(`/api/cases/${id}`)
  },

  create(data: CaseCreate): Promise<Case> {
    return request<Case>('/api/cases', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
  },

  delete(id: string): Promise<void> {
    return request<void>(`/api/cases/${id}`, { method: 'DELETE' })
  },

  /** Fetch a one-shot structured intelligence summary for the Case Snapshot panel. */
  getSummary(id: string): Promise<CaseSummaryResponse> {
    return request<CaseSummaryResponse>(`/api/cases/${id}/summary`)
  },

  /** Extract entity/relationship graph from all READY case documents. Cached server-side; pass forceRefresh=true to re-extract. */
  getGraph(id: string, forceRefresh = false): Promise<GraphResponse> {
    const url = `/api/cases/${id}/graph${forceRefresh ? '?force_refresh=true' : ''}`
    return request<GraphResponse>(url)
  },
}


// ── Documents ─────────────────────────────────────────────────────────────────

export const documentsApi = {
  list(caseId: string): Promise<DocumentListResponse> {
    return request<DocumentListResponse>(`/api/cases/${caseId}/documents`)
  },

  get(documentId: string): Promise<Document> {
    return request<Document>(`/api/documents/${documentId}`)
  },

  getStatus(documentId: string): Promise<DocumentStatus_> {
    return request<DocumentStatus_>(`/api/documents/${documentId}/status`)
  },

  upload(caseId: string, file: File, onProgress?: (pct: number) => void): Promise<Document> {
    return new Promise((resolve, reject) => {
      const formData = new FormData()
      formData.append('file', file)

      const xhr = new XMLHttpRequest()

      if (onProgress) {
        xhr.upload.addEventListener('progress', (e) => {
          if (e.lengthComputable) {
            onProgress(Math.round((e.loaded / e.total) * 100))
          }
        })
      }

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            resolve(JSON.parse(xhr.responseText) as Document)
          } catch {
            reject(new ApiError(xhr.status, 'Invalid JSON response'))
          }
        } else {
          let message = `Upload failed (${xhr.status})`
          try {
            const parsed = JSON.parse(xhr.responseText)
            if (parsed?.detail) message = String(parsed.detail)
          } catch { /* noop */ }
          reject(new ApiError(xhr.status, message))
        }
      })

      xhr.addEventListener('error', () =>
        reject(new ApiError(0, 'Network error during upload')),
      )
      xhr.addEventListener('abort', () =>
        reject(new ApiError(0, 'Upload aborted')),
      )

      xhr.open('POST', `${API_BASE}/api/cases/${caseId}/documents`)
      
      let token = null
      if (typeof window !== 'undefined') {
        token = localStorage.getItem('access_token')
      }
      if (token) {
        xhr.setRequestHeader('Authorization', `Bearer ${token}`)
      }
      
      xhr.send(formData)
    })

  },

  delete(documentId: string): Promise<void> {
    return request<void>(`/api/documents/${documentId}`, { method: 'DELETE' })
  },

  getFileUrl(documentId: string): string {
    return `${API_BASE}/api/documents/${documentId}/file`
  },
}

// ── Chat ──────────────────────────────────────────────────────────────────────────────

export const chatApi = {
  /**
   * Send a message with full conversation history for multi-turn context.
   * The backend uses the history to answer follow-up questions correctly.
   */
  sendMessage(
    caseId: string,
    message: string,
    conversationHistory: ConversationTurn[] = [],
  ): Promise<ChatResponse> {
    return request<ChatResponse>(`/api/cases/${caseId}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        conversation_history: conversationHistory,
      }),
    })
  },

  /**
   * Stream a chat response via Server-Sent Events.
   * Returns an async generator that yields:
   *   { type: 'token', content: string }  — partial text
   *   { type: 'done', sources, model, answer }  — final metadata
   *   { type: 'error', message: string }  — error
   */
  async *sendMessageStream(
    caseId: string,
    message: string,
    conversationHistory: ConversationTurn[] = [],
  ): AsyncGenerator<{ type: string; content?: string; sources?: unknown[]; model?: string; answer?: string; message?: string }> {
    const url = `${API_BASE}/api/cases/${caseId}/chat/stream`
    let token: string | null = null
    if (typeof window !== 'undefined') token = localStorage.getItem('access_token')

    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ message, conversation_history: conversationHistory }),
    })

    if (!res.ok || !res.body) {
      const detail = await res.text()
      throw new ApiError(res.status, detail || `Stream request failed (${res.status})`)
    }

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() ?? ''
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            yield JSON.parse(line.slice(6))
          } catch {
            // malformed chunk — skip
          }
        }
      }
    }
  },
}

// ── Courtroom ─────────────────────────────────────────────────────────────────

export const courtroomApi = {
  submitTurn(
    caseId: string,
    statement: string,
    sessionHistory: SessionTurn[] = [],
    phase = 'arguments',
    judgeTemperament: JudgeTemperament = 'balanced',
  ): Promise<CourtroomResponse> {
    return request<CourtroomResponse>(`/api/cases/${caseId}/courtroom`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        statement,
        session_history: sessionHistory,
        phase,
        judge_temperament: judgeTemperament,
      }),
    })
  },

  getVerdict(
    caseId: string,
    sessionHistory: SessionTurn[] = [],
  ): Promise<VerdictResponse> {
    return request<VerdictResponse>(`/api/cases/${caseId}/courtroom/verdict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_history: sessionHistory }),
    })
  },
}

// ── Trial Prep & Reports ──────────────────────────────────────────────────────

export const reportsApi = {
  getTrialBrief(caseId: string): Promise<TrialBriefResponse> {
    return request<TrialBriefResponse>(`/api/cases/${caseId}/trial-brief`)
  },
}

// ── Legal Precedents & Research ───────────────────────────────────────────────

export const researchApi = {
  queryPrecedents(
    query: string,
    jurisdiction: string = 'Supreme Court of India',
    statute?: string,
  ): Promise<ResearchResponse> {
    return request<ResearchResponse>(`/api/research/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, jurisdiction, statute }),
    })
  },
}

export { ApiError }
