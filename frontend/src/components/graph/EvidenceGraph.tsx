'use client'

import { useEffect, useRef, useState, useCallback, useMemo } from 'react'
import { casesApi } from '@/lib/api'
import type { GraphNode, GraphEdge, GraphResponse, NodeType } from '@/lib/types'
import styles from './EvidenceGraph.module.css'

// ── Node Appearance & Configuration ──────────────────────────────────────────

const NODE_CONFIG: Record<NodeType, { color: string; ring: string; radius: number; emoji: string; label: string; role: string }> = {
  organization: { color: '#6b1e2a', ring: '#9a3040', radius: 32, emoji: '🏛', label: 'Organisation', role: 'Court / Authority' },
  person:       { color: '#c4923a', ring: '#8c6525', radius: 28, emoji: '👤', label: 'Person', role: 'Party / Witness' },
  fact:         { color: '#6b5a2e', ring: '#9a8040', radius: 26, emoji: '⚖', label: 'Fact', role: 'Claim / Allegation' },
  evidence:     { color: '#5a3d6b', ring: '#8050a0', radius: 28, emoji: '📄', label: 'Evidence', role: 'Exhibit / Statute' },
  date:         { color: '#2a5a7a', ring: '#3a7aa0', radius: 22, emoji: '📅', label: 'Date', role: 'Timeline Event' },
  location:     { color: '#3d7a4f', ring: '#50a068', radius: 24, emoji: '📍', label: 'Location', role: 'Place / Jurisdiction' },
}

const EDGE_COLORS: Partial<Record<string, string>> = {
  supports:     '#48a068',
  contradicts:  '#e05555',
  occurred_at:  '#4a90c0',
  filed_by:     '#d4a24a',
  testified_by: '#a07835',
  involves:     '#9a60c0',
  related_to:   '#7a9a4a',
  linked_to:    '#8090a0',
}

export type LayoutMode = 'lanes' | 'orbit'

export interface LayoutNode extends GraphNode {
  x: number
  y: number
  vx: number
  vy: number
  laneIndex?: number
  orderInLane?: number
}

// ── Legal Lane Definitions ───────────────────────────────────────────────────

interface LaneDef {
  key: string
  title: string
  subtitle: string
  types: NodeType[]
  color: string
  borderColor: string
  emoji: string
}

const LANES: LaneDef[] = [
  { key: 'authorities', title: 'Courts & Authorities', subtitle: 'Judicial & Regulatory Bodies', types: ['organization'], color: '#6b1e2a', borderColor: '#9a3040', emoji: '🏛' },
  { key: 'parties', title: 'Parties & Witnesses', subtitle: 'Accused, Petitioners, Witnesses', types: ['person'], color: '#7a5214', borderColor: '#c4923a', emoji: '👤' },
  { key: 'facts', title: 'Claims & Material Facts', subtitle: 'Allegations & Case Facts', types: ['fact'], color: '#52451f', borderColor: '#9a8040', emoji: '⚖' },
  { key: 'evidence', title: 'Evidence & Documents', subtitle: 'Exhibits, Statutes, Reports', types: ['evidence'], color: '#442654', borderColor: '#8050a0', emoji: '📄' },
  { key: 'timeline', title: 'Timeline & Venues', subtitle: 'Critical Dates & Locations', types: ['date', 'location'], color: '#1a415a', borderColor: '#3a7aa0', emoji: '📅' },
]

export interface LaneHeaderInfo {
  key: string
  title: string
  subtitle: string
  emoji: string
  x: number
  y: number
  width: number
  count: number
  color: string
}

export interface OrbitRingInfo {
  r: number
  label: string
  emoji: string
}

// ── Layout Computation Functions ─────────────────────────────────────────────

const CARD_W = 210
const CARD_H = 46
const LANE_GAP = 64
const CARD_GAP_Y = 18

/**
 * Systematic Legal Lanes (Columns) layout.
 * Nodes are strictly arranged into distinct vertical columns by legal role.
 * Zero collisions guaranteed.
 */
function buildLanesLayout(
  nodes: GraphNode[],
  width: number,
  height: number
): { layoutNodes: LayoutNode[]; laneHeaders: LaneHeaderInfo[] } {
  if (nodes.length === 0) return { layoutNodes: [], laneHeaders: [] }

  const activeLanes = LANES.filter(lane => nodes.some(n => lane.types.includes(n.type as NodeType)))
  if (activeLanes.length === 0) return { layoutNodes: [], laneHeaders: [] }

  const totalWidth = activeLanes.length * CARD_W + (activeLanes.length - 1) * LANE_GAP
  const startX = Math.max(60, (width - totalWidth) / 2)
  const headerY = 50
  const startY = 120

  const posMap = new Map<string, { x: number; y: number; laneIndex: number; order: number }>()
  const laneHeaders: LaneHeaderInfo[] = []

  activeLanes.forEach((lane, laneIdx) => {
    const laneCenterX = startX + laneIdx * (CARD_W + LANE_GAP) + CARD_W / 2
    const laneNodes = nodes.filter(n => lane.types.includes(n.type as NodeType))

    laneHeaders.push({
      key: lane.key,
      title: lane.title,
      subtitle: lane.subtitle,
      emoji: lane.emoji,
      x: laneCenterX,
      y: headerY,
      width: CARD_W,
      count: laneNodes.length,
      color: lane.borderColor,
    })

    laneNodes.forEach((node, itemIdx) => {
      const cy = startY + itemIdx * (CARD_H + CARD_GAP_Y) + CARD_H / 2
      posMap.set(node.id, {
        x: laneCenterX,
        y: cy,
        laneIndex: laneIdx,
        order: itemIdx,
      })
    })
  })

  // Fallback for any unassigned node types: place in rightmost column
  nodes.forEach(n => {
    if (!posMap.has(n.id)) {
      const lastIdx = activeLanes.length - 1
      const laneCenterX = startX + lastIdx * (CARD_W + LANE_GAP) + CARD_W / 2
      const existing = Array.from(posMap.values()).filter(p => p.laneIndex === lastIdx).length
      posMap.set(n.id, {
        x: laneCenterX,
        y: startY + existing * (CARD_H + CARD_GAP_Y) + CARD_H / 2,
        laneIndex: lastIdx,
        order: existing,
      })
    }
  })

  const layoutNodes: LayoutNode[] = nodes.map(n => {
    const p = posMap.get(n.id) ?? { x: width / 2, y: height / 2, laneIndex: 0, order: 0 }
    return {
      ...n,
      x: p.x,
      y: p.y,
      vx: 0,
      vy: 0,
      laneIndex: p.laneIndex,
      orderInLane: p.order,
    }
  })

  return { layoutNodes, laneHeaders }
}

const RING_DEFS: { types: NodeType[]; label: string; emoji: string }[] = [
  { types: ['organization'], label: 'Institutions & Authorities', emoji: '🏛' },
  { types: ['person'], label: 'Parties & Witnesses', emoji: '👤' },
  { types: ['evidence', 'fact'], label: 'Evidence & Claims', emoji: '📄' },
  { types: ['date', 'location'], label: 'Timeline & Venues', emoji: '📅' },
]

/**
 * Concentric Orbit layout with guaranteed spacing between rings.
 * Zero collisions between rings or adjacent nodes.
 */
function buildOrbitLayout(
  nodes: GraphNode[],
  width: number,
  height: number
): { layoutNodes: LayoutNode[]; rings: OrbitRingInfo[] } {
  if (nodes.length === 0) return { layoutNodes: [], rings: [] }

  const cx = width / 2
  const cy = height / 2

  const ringBuckets: GraphNode[][] = RING_DEFS.map(() => [])
  const unassigned: GraphNode[] = []

  nodes.forEach(n => {
    let placed = false
    RING_DEFS.forEach((rDef, idx) => {
      if (rDef.types.includes(n.type as NodeType)) {
        ringBuckets[idx].push(n)
        placed = true
      }
    })
    if (!placed) unassigned.push(n)
  })
  ringBuckets[ringBuckets.length - 1].push(...unassigned)

  const posMap = new Map<string, { x: number; y: number }>()
  const rings: OrbitRingInfo[] = []

  let currentR = 0
  const BASE_RING_0 = 150
  const MIN_RING_GAP = 180
  const NODE_MIN_ARC = 130

  ringBuckets.forEach((bucket, ringIdx) => {
    if (bucket.length === 0) return

    if (ringIdx === 0 && bucket.length === 1) {
      posMap.set(bucket[0].id, { x: cx, y: cy })
      currentR = Math.max(currentR, 70)
      return
    }

    const minRForNodes = (bucket.length * NODE_MIN_ARC) / (2 * Math.PI)
    const targetR = Math.max(
      ringIdx === 0 ? BASE_RING_0 : currentR + MIN_RING_GAP,
      minRForNodes
    )
    currentR = targetR

    rings.push({
      r: targetR,
      label: RING_DEFS[ringIdx].label,
      emoji: RING_DEFS[ringIdx].emoji,
    })

    const angleStep = (2 * Math.PI) / bucket.length
    const phase = ringIdx % 2 === 1 ? angleStep / 2 : 0
    const startAngle = -Math.PI / 2 + phase

    bucket.forEach((n, i) => {
      const angle = startAngle + i * angleStep
      posMap.set(n.id, {
        x: cx + targetR * Math.cos(angle),
        y: cy + targetR * Math.sin(angle),
      })
    })
  })

  const layoutNodes: LayoutNode[] = nodes.map(n => {
    const pos = posMap.get(n.id) ?? { x: cx, y: cy }
    return { ...n, x: pos.x, y: pos.y, vx: 0, vy: 0 }
  })

  return { layoutNodes, rings }
}

// ── Component Props & Types ──────────────────────────────────────────────────

interface Props {
  caseId: string
  documentCount: number
}

async function fetchWithRetry<T>(
  fn: () => Promise<T>,
  retries: number = 2,
  delayMs: number = 1500
): Promise<T> {
  let lastError: unknown
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      return await fn()
    } catch (err: any) {
      lastError = err
      if (err?.status === 404 || err?.status === 401) {
        throw err
      }
      if (attempt < retries) {
        await new Promise(r => setTimeout(r, delayMs * (attempt + 1)))
      }
    }
  }
  throw lastError
}

// ── Main Component ──────────────────────────────────────────────────────────

export function EvidenceGraph({ caseId, documentCount }: Props) {
  const [graphData, setGraphData] = useState<GraphResponse | null>(null)
  const [layout, setLayout] = useState<LayoutNode[]>([])
  const [laneHeaders, setLaneHeaders] = useState<LaneHeaderInfo[]>([])
  const [orbitRings, setOrbitRings] = useState<OrbitRingInfo[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [retryCount, setRetryCount] = useState(0)

  // Layout mode & filters
  const [layoutMode, setLayoutMode] = useState<LayoutMode>('lanes')
  const [conflictsOnly, setConflictsOnly] = useState(false)
  const [hiddenTypes, setHiddenTypes] = useState<Set<string>>(new Set())

  // Focus & Inspector state
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null)
  const [hoveredEdgeId, setHoveredEdgeId] = useState<string | null>(null)

  // Pan & Zoom state
  const [transform, setTransform] = useState({ x: 0, y: 0, scale: 1 })
  const isPanning = useRef(false)
  const lastMouse = useRef({ x: 0, y: 0 })

  const svgRef = useRef<SVGSVGElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  // ── Auto-fit Bounding Box Helper ──────────────────────────────────────────
  const fitToScreen = useCallback((nodesToFit: LayoutNode[], padding: number = 60) => {
    if (nodesToFit.length === 0 || !containerRef.current) return
    const cw = containerRef.current.clientWidth || 900
    const ch = containerRef.current.clientHeight || 600

    const xs = nodesToFit.map(n => n.x)
    const ys = nodesToFit.map(n => n.y)
    const minX = Math.min(...xs) - CARD_W / 2 - padding
    const maxX = Math.max(...xs) + CARD_W / 2 + padding
    const minY = Math.min(...ys) - 80 - padding
    const maxY = Math.max(...ys) + CARD_H / 2 + padding

    const graphW = Math.max(maxX - minX, 100)
    const graphH = Math.max(maxY - minY, 100)

    const scaleX = (cw - padding * 2) / graphW
    const scaleY = (ch - padding * 2) / graphH
    const targetScale = Math.min(Math.max(Math.min(scaleX, scaleY), 0.35), 1.15)

    const centerX = (minX + maxX) / 2
    const centerY = (minY + maxY) / 2

    const x = cw / 2 - centerX * targetScale
    const y = ch / 2 - centerY * targetScale

    setTransform({ x, y, scale: targetScale })
  }, [])

  // ── Fetch Graph Data ──────────────────────────────────────────────────────
  const fetchGraph = useCallback(
    async (forceRefresh = false) => {
      setLoading(true)
      setError(null)
      setSelectedNodeId(null)
      setHoveredNodeId(null)
      try {
        const data = await fetchWithRetry(
          () => casesApi.getGraph(caseId, forceRefresh),
          2,
          2000
        )
        setGraphData(data)
        setRetryCount(0)
      } catch (e: any) {
        const msg = e?.message ?? 'Failed to generate evidence graph.'
        setError(msg)
        setRetryCount(prev => prev + 1)
      } finally {
        setLoading(false)
      }
    },
    [caseId]
  )

  useEffect(() => {
    if (documentCount > 0 && !graphData && !loading && !error) {
      fetchGraph(false)
    }
  }, [documentCount, graphData, loading, error, fetchGraph])

  // ── Layout Recalculation Effect ───────────────────────────────────────────
  const recomputeLayout = useCallback(
    (mode: LayoutMode, data: GraphResponse | null) => {
      if (!data || data.nodes.length === 0) {
        setLayout([])
        setLaneHeaders([])
        setOrbitRings([])
        return
      }

      const container = containerRef.current
      const cw = container ? container.clientWidth : 0
      const ch = container ? container.clientHeight : 0
      const w = cw > 0 ? cw : 1000
      const h = ch > 80 ? ch - 80 : 650

      if (mode === 'lanes') {
        const { layoutNodes, laneHeaders: headers } = buildLanesLayout(data.nodes, w, h)
        setLayout(layoutNodes)
        setLaneHeaders(headers)
        setOrbitRings([])
        fitToScreen(layoutNodes, 80)
      } else {
        const { layoutNodes, rings } = buildOrbitLayout(data.nodes, w, h)
        setLayout(layoutNodes)
        setOrbitRings(rings)
        setLaneHeaders([])
        fitToScreen(layoutNodes, 90)
      }
    },
    [fitToScreen]
  )

  useEffect(() => {
    if (!graphData) return
    const timer = setTimeout(() => {
      recomputeLayout(layoutMode, graphData)
    }, 20)
    return () => clearTimeout(timer)
  }, [graphData, layoutMode, recomputeLayout])

  // ── Node Dragging Handlers ────────────────────────────────────────────────
  const draggedNodeId = useRef<string | null>(null)
  const dragStartMouse = useRef({ x: 0, y: 0 })
  const dragNodeStartPos = useRef({ x: 0, y: 0 })
  const [activeDragId, setActiveDragId] = useState<string | null>(null)

  const onNodeMouseDown = (e: React.MouseEvent, nodeId: string) => {
    e.stopPropagation()
    draggedNodeId.current = nodeId
    setActiveDragId(nodeId)
    dragStartMouse.current = { x: e.clientX, y: e.clientY }
    const node = layout.find(n => n.id === nodeId)
    if (node) {
      dragNodeStartPos.current = { x: node.x, y: node.y }
    }
  }

  // ── Pan and Drag Canvas Handlers ──────────────────────────────────────────
  const onMouseDown = (e: React.MouseEvent) => {
    if (e.target !== svgRef.current && !(e.target as SVGElement).classList?.contains?.('bg')) return
    isPanning.current = true
    lastMouse.current = { x: e.clientX, y: e.clientY }
    // Clicking empty background deselects active node
    setSelectedNodeId(null)
  }

  const onMouseMove = (e: React.MouseEvent) => {
    if (draggedNodeId.current) {
      const scale = transform.scale || 1
      const dx = (e.clientX - dragStartMouse.current.x) / scale
      const dy = (e.clientY - dragStartMouse.current.y) / scale
      const targetId = draggedNodeId.current

      setLayout(prev =>
        prev.map(n =>
          n.id === targetId
            ? { ...n, x: dragNodeStartPos.current.x + dx, y: dragNodeStartPos.current.y + dy }
            : n
        )
      )
      return
    }

    if (!isPanning.current) return
    const dx = e.clientX - lastMouse.current.x
    const dy = e.clientY - lastMouse.current.y
    lastMouse.current = { x: e.clientX, y: e.clientY }
    setTransform(t => ({ ...t, x: t.x + dx, y: t.y + dy }))
  }

  const onMouseUp = () => {
    isPanning.current = false
    draggedNodeId.current = null
    setActiveDragId(null)
  }

  const onWheel = (e: React.WheelEvent) => {
    e.preventDefault()
    const delta = e.deltaY < 0 ? 1.12 : 0.89
    setTransform(t => ({
      ...t,
      scale: Math.max(0.2, Math.min(3.2, t.scale * delta)),
    }))
  }

  const resetView = () => fitToScreen(layout, 80)
  const centerView = () => setTransform({ x: 0, y: 0, scale: 1 })

  // ── Active Node Filtering ─────────────────────────────────────────────────
  const contradictionEdges = useMemo(() => {
    if (!graphData) return []
    return graphData.edges.filter(e => e.type === 'contradicts')
  }, [graphData])

  const contradictionNodeIds = useMemo(() => {
    const ids = new Set<string>()
    contradictionEdges.forEach(e => {
      ids.add(e.source)
      ids.add(e.target)
    })
    return ids
  }, [contradictionEdges])

  // Filtered nodes
  const visibleLayout = useMemo(() => {
    return layout.filter(n => {
      if (hiddenTypes.has(n.type)) return false
      if (conflictsOnly && !contradictionNodeIds.has(n.id)) return false
      return true
    })
  }, [layout, hiddenTypes, conflictsOnly, contradictionNodeIds])

  const visibleIds = useMemo(() => new Set(visibleLayout.map(n => n.id)), [visibleLayout])

  // Filtered edges
  const visibleEdges = useMemo(() => {
    if (!graphData) return []
    return graphData.edges.filter(e => {
      if (!visibleIds.has(e.source) || !visibleIds.has(e.target)) return false
      if (conflictsOnly && e.type !== 'contradicts') return false
      return true
    })
  }, [graphData, visibleIds, conflictsOnly])

  const nodeMap = useMemo(() => {
    const map = new Map<string, LayoutNode>()
    layout.forEach(n => map.set(n.id, n))
    return map
  }, [layout])

  // Active focus entity (from hover or selection)
  const activeFocusId = selectedNodeId || hoveredNodeId

  const focusedConnectedNodeIds = useMemo(() => {
    if (!activeFocusId || !graphData) return new Set<string>()
    const connected = new Set<string>([activeFocusId])
    graphData.edges.forEach(e => {
      if (e.source === activeFocusId) connected.add(e.target)
      if (e.target === activeFocusId) connected.add(e.source)
    })
    return connected
  }, [activeFocusId, graphData])

  const selectedNode = useMemo(() => {
    if (!selectedNodeId) return null
    return nodeMap.get(selectedNodeId) ?? null
  }, [selectedNodeId, nodeMap])

  const selectedNodeConnections = useMemo(() => {
    if (!selectedNodeId || !graphData) return []
    const conns: { edge: GraphEdge; otherNode: GraphNode; isOutgoing: boolean }[] = []
    graphData.edges.forEach(e => {
      if (e.source === selectedNodeId) {
        const other = graphData.nodes.find(n => n.id === e.target)
        if (other) conns.push({ edge: e, otherNode: other, isOutgoing: true })
      } else if (e.target === selectedNodeId) {
        const other = graphData.nodes.find(n => n.id === e.source)
        if (other) conns.push({ edge: e, otherNode: other, isOutgoing: false })
      }
    })
    return conns
  }, [selectedNodeId, graphData])

  const toggleType = (type: string) => {
    setHiddenTypes(prev => {
      const next = new Set(prev)
      if (next.has(type)) next.delete(type)
      else next.add(type)
      return next
    })
  }

  // ── Empty / Loading / Error States ────────────────────────────────────────
  if (!graphData && !loading && !error) {
    return (
      <div className={styles.container}>
        <div className={styles.stateContainer}>
          <div className={styles.stateIcon}>⚖</div>
          <p className={styles.stateTitle}>Evidence Knowledge Graph</p>
          <p className={styles.stateDesc}>
            {documentCount === 0
              ? 'Upload and process case documents to generate the evidence graph.'
              : `${documentCount} document${documentCount !== 1 ? 's' : ''} ready. Extract an interactive knowledge map connecting persons, authorities, evidence, and timeline facts.`}
          </p>
          <button
            className="btn btn-primary"
            onClick={() => fetchGraph(false)}
            id="generate-graph-btn"
          >
            Generate Evidence Graph
          </button>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className={styles.container}>
        <div className={styles.stateContainer}>
          <div className={styles.loadingRow}>
            <span className="spinner" style={{ width: 22, height: 22 }} />
            <span style={{ fontSize: '0.95rem', fontWeight: 500 }}>
              Extracting entities and mapping legal relationships…
            </span>
          </div>
          <p className={styles.stateDesc} style={{ marginTop: 12 }}>
            Court Vision AI is cross-referencing testimonies, statutory sections, dates, and evidence
            to construct an organized legal knowledge graph.
          </p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={styles.container}>
        <div className={styles.stateContainer}>
          <div className={styles.stateIcon} style={{ color: '#c45a5a' }}>⚠</div>
          <p className={styles.stateTitle}>Graph Generation Failed</p>
          <p className={styles.stateDesc}>{error}</p>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', justifyContent: 'center' }}>
            <button className="btn btn-secondary" onClick={() => fetchGraph(true)}>
              ↺ Try Again
            </button>
            {retryCount >= 2 && (
              <button className="btn btn-primary" onClick={() => fetchGraph(true)}>
                Force Re-extract
              </button>
            )}
          </div>
        </div>
      </div>
    )
  }

  if (graphData && graphData.nodes.length === 0) {
    return (
      <div className={styles.container}>
        <div className={styles.stateContainer}>
          <div className={styles.stateIcon}>◌</div>
          <p className={styles.stateTitle}>No entities found</p>
          <p className={styles.stateDesc}>
            The AI could not identify entities in the current documents. Try uploading complete case documents or FIR files.
          </p>
          <button className="btn btn-secondary" onClick={() => fetchGraph(true)}>
            Retry Extraction
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.container} ref={containerRef}>
      {/* ── Toolbar ────────────────────────────────────────────────────────── */}
      <div className={styles.toolbar}>
        <span className={styles.toolbarTitle}>Evidence Graph</span>

        {/* View Mode Switcher */}
        <div className={styles.viewModeGroup}>
          <button
            className={`${styles.modeBtn} ${layoutMode === 'lanes' ? styles.modeBtnActive : ''}`}
            onClick={() => setLayoutMode('lanes')}
            title="Systematic Legal Lanes (Columns by category)"
          >
            <span>⊞</span> Legal Lanes
          </button>
          <button
            className={`${styles.modeBtn} ${layoutMode === 'orbit' ? styles.modeBtnActive : ''}`}
            onClick={() => setLayoutMode('orbit')}
            title="Concentric Radar Orbit view"
          >
            <span>◯</span> Orbit View
          </button>
        </div>

        {/* Conflict Filter Toggle */}
        <button
          className={`${styles.conflictFilterBtn} ${conflictsOnly ? styles.conflictFilterBtnActive : ''}`}
          onClick={() => setConflictsOnly(prev => !prev)}
          title="Filter to show only conflicting testimonies and contradictory evidence"
        >
          <span>⚠</span>
          <span>Conflicts {contradictionEdges.length > 0 ? `(${contradictionEdges.length})` : 'None'}</span>
        </button>

        {/* Legend / Category Filter Chips */}
        <div className={styles.legend}>
          {(Object.entries(NODE_CONFIG) as [NodeType, typeof NODE_CONFIG[NodeType]][]).map(([type, cfg]) => {
            const hidden = hiddenTypes.has(type)
            const count = layout.filter(n => n.type === type).length
            if (count === 0) return null
            return (
              <button
                key={type}
                className={styles.legendItem}
                onClick={() => toggleType(type)}
                style={{
                  opacity: hidden ? 0.35 : 1,
                  border: hidden ? '1px dashed rgba(255,255,255,0.2)' : '1px solid transparent',
                  textDecoration: hidden ? 'line-through' : 'none',
                  cursor: 'pointer',
                  background: 'none',
                  padding: '3px 6px',
                  borderRadius: 4,
                }}
                title={hidden ? `Show ${cfg.label} (${count})` : `Hide ${cfg.label} (${count})`}
              >
                <span className={styles.legendDot} style={{ background: cfg.color }} />
                <span>{cfg.label}</span>
                <span style={{ opacity: 0.6, fontSize: '0.6rem' }}>({count})</span>
              </button>
            )
          })}
        </div>

        {/* Action Controls */}
        <div className={styles.toolbarActions}>
          <button className={styles.iconBtn} onClick={resetView} title="Fit entire graph to screen">
            ⛶ Fit
          </button>
          <button className={styles.iconBtn} onClick={centerView} title="Center view (100% scale)">
            ⊙ Center
          </button>
          <button
            className={styles.iconBtn}
            onClick={() => setTransform(t => ({ ...t, scale: Math.min(3.2, t.scale * 1.25) }))}
            title="Zoom in"
          >
            + Zoom
          </button>
          <button
            className={styles.iconBtn}
            onClick={() => setTransform(t => ({ ...t, scale: Math.max(0.2, t.scale * 0.8) }))}
            title="Zoom out"
          >
            − Zoom
          </button>
          <button
            className={styles.iconBtn}
            onClick={() => fetchGraph(true)}
            title="Re-extract fresh knowledge graph from case files"
          >
            ↺ Refresh
          </button>
        </div>
      </div>

      {/* ── SVG Canvas ─────────────────────────────────────────────────────── */}
      <div
        className={styles.canvas}
        onMouseDown={onMouseDown}
        onMouseMove={onMouseMove}
        onMouseUp={onMouseUp}
        onMouseLeave={onMouseUp}
        onWheel={onWheel}
      >
        <svg ref={svgRef} className={styles.svgCanvas}>
          <defs>
            <marker id="arrowhead" markerWidth="9" markerHeight="6" refX="8" refY="3" orient="auto">
              <polygon points="0 0, 9 3, 0 6" fill="rgba(196, 170, 130, 0.6)" />
            </marker>
            <marker id="arrowhead-contradiction" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
              <polygon points="0 0, 10 3.5, 0 7" fill="#e05555" />
            </marker>
            <marker id="arrowhead-highlight" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
              <polygon points="0 0, 10 3.5, 0 7" fill="#c4923a" />
            </marker>

            <filter id="node-glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="5" result="coloredBlur" />
              <feMerge>
                <feMergeNode in="coloredBlur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            <filter id="conflict-glow" x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur stdDeviation="6" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Background capture area for easy pan */}
          <rect className="bg" width="100%" height="100%" fill="transparent" />

          <g transform={`translate(${transform.x},${transform.y}) scale(${transform.scale})`}>
            {/* ── Lane Headers (in Lanes Mode) ─────────────────────────────── */}
            {layoutMode === 'lanes' &&
              laneHeaders.map(hdr => (
                <g key={hdr.key} transform={`translate(${hdr.x},${hdr.y})`}>
                  {/* Subtle column background track */}
                  <rect
                    x={-hdr.width / 2 - 8}
                    y={-10}
                    width={hdr.width + 16}
                    height={46}
                    rx={8}
                    fill="rgba(255, 255, 255, 0.02)"
                    stroke="rgba(255, 255, 255, 0.07)"
                    strokeWidth={1}
                  />
                  {/* Emoji & Title */}
                  <text
                    textAnchor="middle"
                    dominantBaseline="middle"
                    y={6}
                    fontSize={11.5}
                    fontWeight={700}
                    fontFamily="Inter, system-ui, sans-serif"
                    fill="rgba(255, 255, 255, 0.95)"
                    letterSpacing={0.4}
                  >
                    {hdr.emoji} {hdr.title}{' '}
                    <tspan fill={hdr.color} fontWeight={700}>
                      ({hdr.count})
                    </tspan>
                  </text>
                  {/* Subtitle */}
                  <text
                    textAnchor="middle"
                    dominantBaseline="middle"
                    y={22}
                    fontSize={8.5}
                    fontFamily="Inter, system-ui, sans-serif"
                    fill="rgba(255, 255, 255, 0.45)"
                  >
                    {hdr.subtitle}
                  </text>
                </g>
              ))}

            {/* ── Orbit Tracks (in Orbit Mode) ─────────────────────────────── */}
            {layoutMode === 'orbit' &&
              orbitRings.map((ring, idx) => {
                const cw = containerRef.current?.clientWidth || 1000
                const ch = containerRef.current?.clientHeight || 650
                const cx = cw / 2
                const cy = ch / 2
                return (
                  <g key={idx}>
                    <circle
                      cx={cx}
                      cy={cy}
                      r={ring.r}
                      fill="none"
                      stroke="rgba(196, 146, 58, 0.12)"
                      strokeWidth={1}
                      strokeDasharray="5 7"
                    />
                    {/* Ring Label at top apex */}
                    <rect
                      x={cx - 100}
                      y={cy - ring.r - 11}
                      width={200}
                      height={18}
                      rx={9}
                      fill="rgba(14, 16, 24, 0.9)"
                      stroke="rgba(196, 146, 58, 0.25)"
                      strokeWidth={0.8}
                    />
                    <text
                      x={cx}
                      y={cy - ring.r - 2}
                      textAnchor="middle"
                      dominantBaseline="middle"
                      fontSize={9}
                      fontWeight={600}
                      fontFamily="Inter, system-ui, sans-serif"
                      fill="rgba(212, 162, 74, 0.85)"
                      letterSpacing={0.5}
                    >
                      {ring.emoji} {ring.label.toUpperCase()}
                    </text>
                  </g>
                )
              })}

            {/* ── Edges ───────────────────────────────────────────────────── */}
            {visibleEdges.map(edge => {
              const src = nodeMap.get(edge.source)
              const tgt = nodeMap.get(edge.target)
              if (!src || !tgt) return null

              const isContradiction = edge.type === 'contradicts'
              const isHovered = hoveredEdgeId === edge.id
              const isDirectlyFocused =
                activeFocusId && (edge.source === activeFocusId || edge.target === activeFocusId)

              // Compute opacity based on focus state
              let opacity = 0.4
              if (activeFocusId) {
                opacity = isDirectlyFocused ? 1 : 0.08
              } else if (isContradiction) {
                opacity = 0.9
              } else if (isHovered) {
                opacity = 1
              }

              const edgeColor = isContradiction
                ? '#e05555'
                : isDirectlyFocused
                ? '#d4a24a'
                : EDGE_COLORS[edge.type] ?? 'rgba(180,180,200,0.4)'

              const strokeW = isContradiction ? 2.5 : isDirectlyFocused || isHovered ? 2.2 : 1.4

              // Path computation
              let pathD = ''
              let labelX = 0
              let labelY = 0

              if (layoutMode === 'lanes') {
                // Connect cards at horizontal boundaries
                const dx = tgt.x - src.x
                const srcX = dx >= 0 ? src.x + CARD_W / 2 : src.x - CARD_W / 2
                const tgtX = dx >= 0 ? tgt.x - CARD_W / 2 : tgt.x + CARD_W / 2
                const srcY = src.y
                const tgtY = tgt.y

                if (Math.abs(src.x - tgt.x) < 10) {
                  // Same lane: curved vertical loop
                  const loopOffset = 55
                  const midY = (srcY + tgtY) / 2
                  pathD = `M ${src.x + CARD_W / 2} ${srcY} C ${src.x + CARD_W / 2 + loopOffset} ${srcY}, ${src.x + CARD_W / 2 + loopOffset} ${tgtY}, ${src.x + CARD_W / 2} ${tgtY}`
                  labelX = src.x + CARD_W / 2 + loopOffset * 0.75
                  labelY = midY
                } else {
                  // Across lanes: smooth horizontal S-curve
                  const curveSpan = Math.abs(tgtX - srcX) * 0.45
                  const cpx1 = srcX + (dx >= 0 ? curveSpan : -curveSpan)
                  const cpx2 = tgtX - (dx >= 0 ? curveSpan : -curveSpan)
                  pathD = `M ${srcX} ${srcY} C ${cpx1} ${srcY}, ${cpx2} ${tgtY}, ${tgtX} ${tgtY}`
                  labelX = (srcX + tgtX) / 2
                  labelY = (srcY + tgtY) / 2
                }
              } else {
                // Orbit mode: bezier curve
                const mx = (src.x + tgt.x) / 2
                const my = (src.y + tgt.y) / 2
                const edgeLen = Math.sqrt((tgt.x - src.x) ** 2 + (tgt.y - src.y) ** 2) || 1
                const nx = -(tgt.y - src.y) / edgeLen
                const ny = (tgt.x - src.x) / edgeLen
                const curvature = isContradiction ? 55 : 30
                const cpx = mx + nx * curvature
                const cpy = my + ny * curvature

                pathD = `M ${src.x} ${src.y} Q ${cpx} ${cpy} ${tgt.x} ${tgt.y}`
                labelX = (src.x + 2 * cpx + tgt.x) / 4
                labelY = (src.y + 2 * cpy + tgt.y) / 4
              }

              const markerId = isContradiction
                ? 'url(#arrowhead-contradiction)'
                : isDirectlyFocused
                ? 'url(#arrowhead-highlight)'
                : 'url(#arrowhead)'

              return (
                <g
                  key={edge.id}
                  onMouseEnter={() => setHoveredEdgeId(edge.id)}
                  onMouseLeave={() => setHoveredEdgeId(null)}
                  style={{ cursor: 'pointer' }}
                >
                  {/* Invisible hit path */}
                  <path d={pathD} fill="none" stroke="transparent" strokeWidth={18} />

                  {/* Visible edge line */}
                  <path
                    d={pathD}
                    fill="none"
                    stroke={edgeColor}
                    strokeWidth={strokeW}
                    strokeDasharray={isContradiction ? '6 3' : undefined}
                    opacity={opacity}
                    markerEnd={markerId}
                    filter={isContradiction ? 'url(#conflict-glow)' : undefined}
                    style={{ transition: 'opacity 0.2s, stroke-width 0.2s, stroke 0.2s' }}
                  />

                  {/* Label shown on hover or when directly focused */}
                  {(isHovered || isDirectlyFocused) && !isContradiction && (
                    <g transform={`translate(${labelX},${labelY})`}>
                      <rect
                        x={-42}
                        y={-10}
                        width={84}
                        height={18}
                        rx={4}
                        fill="rgba(10, 12, 18, 0.92)"
                        stroke={edgeColor}
                        strokeWidth={0.8}
                      />
                      <text
                        x={0}
                        y={1}
                        textAnchor="middle"
                        dominantBaseline="middle"
                        fill={edgeColor}
                        fontSize={9.5}
                        fontFamily="Inter, system-ui, sans-serif"
                        fontWeight={600}
                      >
                        {edge.label ?? edge.type}
                      </text>
                    </g>
                  )}

                  {/* Prominent contradiction pill */}
                  {isContradiction && (
                    <g transform={`translate(${labelX},${labelY})`}>
                      <rect
                        x={-50}
                        y={-11}
                        width={100}
                        height={20}
                        rx={10}
                        fill="#8a1e1e"
                        stroke="#e05555"
                        strokeWidth={1.2}
                      />
                      <text
                        x={0}
                        y={1}
                        textAnchor="middle"
                        dominantBaseline="middle"
                        fill="#ffffff"
                        fontSize={9}
                        fontFamily="Inter, system-ui, sans-serif"
                        fontWeight={700}
                        letterSpacing={0.5}
                      >
                        ⚠ CONTRADICTION
                      </text>
                    </g>
                  )}
                </g>
              )
            })}

            {/* ── Nodes (Legal Cards / Pills) ──────────────────────────────── */}
            {visibleLayout.map(node => {
              const cfg = NODE_CONFIG[node.type as NodeType] ?? NODE_CONFIG.fact
              const isSelected = selectedNodeId === node.id
              const isHovered = hoveredNodeId === node.id
              const isDragging = activeDragId === node.id

              // Determine dimming if another entity is active
              let nodeOpacity = 1
              if (activeFocusId) {
                nodeOpacity = focusedConnectedNodeIds.has(node.id) ? 1 : 0.22
              }

              // Card width and height
              const isOrbit = layoutMode === 'orbit'
              const nodeW = isOrbit ? 144 : CARD_W
              const nodeH = isOrbit ? 36 : CARD_H
              const rx = isOrbit ? 18 : 9

              // Format text nicely
              const maxChars = isOrbit ? 14 : 22
              const displayLabel =
                node.label.length > maxChars ? node.label.slice(0, maxChars - 1) + '…' : node.label

              return (
                <g
                  key={node.id}
                  transform={`translate(${node.x},${node.y})`}
                  opacity={nodeOpacity}
                  className={`${styles.nodeGroup} ${isDragging ? styles.nodeDragging : ''}`}
                  onMouseDown={e => onNodeMouseDown(e, node.id)}
                  onClick={e => {
                    e.stopPropagation()
                    setSelectedNodeId(prev => (prev === node.id ? null : node.id))
                  }}
                  onMouseEnter={() => setHoveredNodeId(node.id)}
                  onMouseLeave={() => setHoveredNodeId(null)}
                  style={{ cursor: 'pointer', transition: 'opacity 0.2s' }}
                >
                  {/* Selection / hover outer glow */}
                  {(isSelected || isHovered) && (
                    <rect
                      x={-nodeW / 2 - 3}
                      y={-nodeH / 2 - 3}
                      width={nodeW + 6}
                      height={nodeH + 6}
                      rx={rx + 2}
                      fill="none"
                      stroke={cfg.color}
                      strokeWidth={2}
                      filter="url(#node-glow)"
                    />
                  )}

                  {/* Card Background */}
                  <rect
                    x={-nodeW / 2}
                    y={-nodeH / 2}
                    width={nodeW}
                    height={nodeH}
                    rx={rx}
                    fill={isSelected ? '#1f2433' : '#121520'}
                    stroke={isSelected ? '#d4a24a' : cfg.ring}
                    strokeWidth={isSelected ? 2 : 1.3}
                  />

                  {/* Left Icon Badge Circle */}
                  <circle
                    cx={-nodeW / 2 + (isOrbit ? 18 : 20)}
                    cy={0}
                    r={isOrbit ? 11 : 13}
                    fill={cfg.color}
                    opacity={0.85}
                  />
                  <text
                    x={-nodeW / 2 + (isOrbit ? 18 : 20)}
                    y={isOrbit ? 1 : 1.5}
                    textAnchor="middle"
                    dominantBaseline="middle"
                    fontSize={isOrbit ? 10 : 12}
                  >
                    {cfg.emoji}
                  </text>

                  {/* Title Label */}
                  <text
                    x={-nodeW / 2 + (isOrbit ? 35 : 40)}
                    y={isOrbit ? 1 : -4}
                    textAnchor="start"
                    dominantBaseline="middle"
                    fontSize={isOrbit ? 10 : 11}
                    fontWeight={600}
                    fontFamily="Inter, system-ui, sans-serif"
                    fill="rgba(255, 255, 255, 0.95)"
                  >
                    {displayLabel}
                  </text>

                  {/* Subtitle / Role Tag (in Lanes mode) */}
                  {!isOrbit && (
                    <text
                      x={-nodeW / 2 + 40}
                      y={9}
                      textAnchor="start"
                      dominantBaseline="middle"
                      fontSize={8}
                      fontFamily="Inter, system-ui, sans-serif"
                      fill={cfg.color}
                      fontWeight={500}
                      letterSpacing={0.4}
                      style={{ textTransform: 'uppercase' }}
                    >
                      {cfg.role}
                    </text>
                  )}
                </g>
              )
            })}
          </g>
        </svg>

        {/* ── Entity Intelligence Inspector Panel ───────────────────────────── */}
        {selectedNode && (
          <div className={styles.inspector}>
            <div className={styles.inspectorHeader}>
              <div
                className={styles.inspectorTag}
                style={{
                  background: `${NODE_CONFIG[selectedNode.type as NodeType]?.color}33`,
                  color: NODE_CONFIG[selectedNode.type as NodeType]?.ring,
                  border: `1px solid ${NODE_CONFIG[selectedNode.type as NodeType]?.ring}55`,
                }}
              >
                <span>{NODE_CONFIG[selectedNode.type as NodeType]?.emoji}</span>
                <span>{NODE_CONFIG[selectedNode.type as NodeType]?.label}</span>
              </div>
              <button
                className={styles.inspectorClose}
                onClick={() => setSelectedNodeId(null)}
                title="Close Inspector"
              >
                ✕
              </button>
            </div>

            <h3 className={styles.inspectorTitle}>{selectedNode.label}</h3>

            {selectedNode.description ? (
              <p className={styles.inspectorDesc}>{selectedNode.description}</p>
            ) : (
              <p className={styles.inspectorDesc} style={{ fontStyle: 'italic', opacity: 0.6 }}>
                Entity extracted from case documents.
              </p>
            )}

            {selectedNode.document_sources && selectedNode.document_sources.length > 0 && (
              <div style={{ marginBottom: 12 }}>
                <p className={styles.inspectorSectionTitle}>Source Documents</p>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                  {selectedNode.document_sources.map((src, i) => (
                    <span
                      key={i}
                      style={{
                        fontSize: '0.7rem',
                        background: 'rgba(255,255,255,0.06)',
                        padding: '2px 6px',
                        borderRadius: 4,
                        color: 'var(--text-muted)',
                      }}
                    >
                      📎 {src}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Direct Legal Connections */}
            <div>
              <p className={styles.inspectorSectionTitle}>
                Connected Relationships ({selectedNodeConnections.length})
              </p>
              {selectedNodeConnections.length === 0 ? (
                <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                  No explicit relationships recorded.
                </p>
              ) : (
                <div className={styles.inspectorConnectionList}>
                  {selectedNodeConnections.map(({ edge, otherNode, isOutgoing }, i) => {
                    const isContradiction = edge.type === 'contradicts'
                    return (
                      <div
                        key={i}
                        className={styles.inspectorConnItem}
                        style={{
                          borderColor: isContradiction ? '#e05555' : 'var(--border)',
                          background: isContradiction ? 'rgba(224, 85, 85, 0.08)' : undefined,
                          cursor: 'pointer',
                        }}
                        onClick={() => setSelectedNodeId(otherNode.id)}
                        title={`Click to focus on ${otherNode.label}`}
                      >
                        <div className={styles.inspectorConnName}>
                          <span style={{ marginRight: 6 }}>
                            {NODE_CONFIG[otherNode.type as NodeType]?.emoji ?? '•'}
                          </span>
                          <span>{otherNode.label}</span>
                        </div>
                        <div
                          className={styles.inspectorConnRel}
                          style={{ color: isContradiction ? '#ff8080' : undefined }}
                        >
                          {isContradiction ? '⚠ CONFLICT' : (isOutgoing ? `→ ${edge.label}` : `← ${edge.label}`)}
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* ── Bottom Stats Bar ───────────────────────────────────────────────── */}
      <div className={styles.statsBar}>
        <span className={styles.stat}>
          <strong>{visibleLayout.length}</strong> / {layout.length} entities
        </span>
        <span className={styles.stat}>
          <strong>{visibleEdges.length}</strong> relationships
        </span>
        <span
          className={styles.stat}
          style={{ color: contradictionEdges.length > 0 ? '#ff8080' : 'var(--text-muted)' }}
        >
          <strong>{contradictionEdges.length}</strong> contradictions
        </span>
        <span className={styles.stat}>
          <strong>{graphData?.document_count}</strong> docs
        </span>
        <span
          className={styles.stat}
          style={{ marginLeft: 'auto', color: 'var(--text-dim)', fontSize: '0.7rem' }}
        >
          Click card = inspect &amp; focus · Drag canvas = pan · Scroll = zoom · Toggle lanes/orbit in toolbar
        </span>
      </div>
    </div>
  )
}
