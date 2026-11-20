/**
 * Court Vision AI — Shared TypeScript Types
 * Aligned with backend Pydantic schemas.
 */

export type CaseType =
  | 'criminal'
  | 'civil'
  | 'constitutional'
  | 'corporate'
  | 'family'
  | 'intellectual_property'
  | 'labour'
  | 'tax'
  | 'other'

export type CaseStatus = 'preparing' | 'active' | 'archived' | 'closed'
export type UserCaseRole = 'defence' | 'prosecution' | 'researcher' | 'student'
export type DocumentStatus = 'uploading' | 'processing' | 'ready' | 'failed'

export interface Case {
  id: string
  name: string
  case_type: CaseType
  description: string | null
  case_number: string | null
  user_role: UserCaseRole
  status: CaseStatus
  owner_id: string
  document_count: number
  created_at: string
  updated_at: string
}

export interface CaseCreate {
  name: string
  case_type: CaseType
  description?: string
  case_number?: string
  user_role: UserCaseRole
}

export interface Document {
  id: string
  case_id: string
  original_name: string
  mime_type: string
  file_size: number
  page_count: number | null
  status: DocumentStatus
  error_message: string | null
  uploaded_at: string
  processed_at: string | null
  updated_at: string
}

export interface DocumentStatus_ {
  id: string
  status: DocumentStatus
  page_count: number | null
  error_message: string | null
  processed_at: string | null
}

export interface CaseListResponse {
  cases: Case[]
  total: number
}

export interface DocumentListResponse {
  documents: Document[]
  total: number
}

export const CASE_TYPE_LABELS: Record<CaseType, string> = {
  criminal: 'Criminal',
  civil: 'Civil',
  constitutional: 'Constitutional',
  corporate: 'Corporate',
  family: 'Family',
  intellectual_property: 'Intellectual Property',
  labour: 'Labour',
  tax: 'Tax',
  other: 'Other',
}

export const ROLE_LABELS: Record<UserCaseRole, string> = {
  defence: 'Defence',
  prosecution: 'Prosecution',
  researcher: 'Researcher',
  student: 'Student / Moot Court',
}

export const STATUS_LABELS: Record<CaseStatus, string> = {
  preparing: 'Preparing',
  active: 'Active',
  archived: 'Archived',
  closed: 'Closed',
}

// ── Chat / Case Intelligence ─────────────────────────────────────────────────

export interface ChatSource {
  document_id: string
  document_name: string
  excerpt: string
  page_hint: string | null
}

export interface ChatResponse {
  answer: string
  sources: ChatSource[]
  model: string
  tokens_used: number | null
  has_documents: boolean
}

export interface CaseSummaryResponse {
  overview: string
  key_issues: string[]
  important_facts: string[]
  important_dates: string[]
  evidence: string[]
  potential_weaknesses: string[]
  recommended_next_steps: string[]
  has_documents: boolean
}

export type ChatRole = 'user' | 'assistant'

/** A serialized turn sent to the backend for multi-turn context retention */
export interface ConversationTurn {
  role: ChatRole
  content: string
}

/** A UI message bubble (richer than ConversationTurn) */
export interface ChatMessage {
  id: string
  role: ChatRole
  content: string
  sources?: ChatSource[]
  model?: string
  timestamp: Date
  isLoading?: boolean
  isError?: boolean
}

// ── Evidence Graph ────────────────────────────────────────────────────────────

export type NodeType = 'person' | 'organization' | 'date' | 'location' | 'fact' | 'evidence'
export type EdgeType =
  | 'involved_in'
  | 'related_to'
  | 'occurred_at'
  | 'supports'
  | 'contradicts'
  | 'filed_by'
  | 'testified_by'
  | 'linked_to'

export interface GraphNode {
  id: string
  label: string
  type: NodeType
  description?: string
  document_sources?: string[]
}

export interface GraphEdge {
  id: string
  source: string
  target: string
  type: EdgeType
  label: string
}

export interface GraphResponse {
  nodes: GraphNode[]
  edges: GraphEdge[]
  has_documents: boolean
  document_count: number
}

// ── Virtual Courtroom ─────────────────────────────────────────────────────────

export type TrialPhase = 'opening' | 'examination' | 'arguments' | 'closing'
export type CourtroomSpeaker = 'lawyer' | 'judge' | 'opposing' | 'system'
export type JudgeTemperament = 'strict' | 'inquisitive' | 'balanced'

export interface SessionTurn {
  speaker: CourtroomSpeaker
  content: string
}

export interface CourtroomResponse {
  judge_response: string
  opposing_response: string
  phase: string
  turn_number: number
}

export interface Scorecard {
  overall_score: number
  legal_reasoning_score: number
  evidence_grounding_score: number
  courtroom_decorum_score: number
  strengths: string[]
  areas_for_improvement: string[]
  mentor_notes: string
}

export interface VerdictResponse {
  verdict: string
  outcome: string
  reasoning: string
  key_findings: string[]
  scorecard?: Scorecard
}

// ── Trial Prep & Reports ──────────────────────────────────────────────────────

export interface ChronologyItem {
  date: string
  event: string
  significance: string
  source?: string
}

export interface CrossExamQuestion {
  question: string
  objective: string
  contradiction?: string
}

export interface WitnessCrossExam {
  witness: string
  role?: string
  questions: CrossExamQuestion[]
}

export interface RelatedPrecedent {
  case_title: string
  citation: string | null
  court: string | null
  ratio_decidendi: string | null
  source_document: string
  page: number | null
}

export interface TrialBriefResponse {
  case_id: string
  case_title: string
  chronology: ChronologyItem[]
  cross_examination: WitnessCrossExam[]
  synopsis: string
  doc_count: number
  pages_indexed?: number
  related_precedents?: RelatedPrecedent[]
  model?: string
  errors?: string[]
}

// ── Indian Legal Precedents & Research ────────────────────────────────────────

export interface Precedent {
  case_title: string
  citation: string
  court: string
  bench_size?: string
  ratio_decidendi: string
  key_quote: string
  application_guidance: string
  statutory_provisions?: string[]
  /** "library" = from a judgment uploaded to Court Vision (or a case it cites); "ai" = suggested by the model */
  source?: 'library' | 'ai'
  source_document?: string | null
  page?: number | null
  passage?: string | null
  /** true = AI-suggested citation not found in the library; verify before citing */
  verify?: boolean
}

export interface ResearchResponse {
  query: string
  key_principles: string[]
  statutory_provisions: string[]
  precedents: Precedent[]
  argument_strategy: string
  library_count?: number
  ai_count?: number
  library_size?: number
  /** AI suggestions not found in the library — shown separately, must be verified before use */
  unverified_leads?: Precedent[]
  warnings?: string[]
}

