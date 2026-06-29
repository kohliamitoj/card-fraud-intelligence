import { useEffect, useState, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ChevronLeft, Send, RefreshCw, MessageSquare, StickyNote, Settings2 } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import client from '../api/client'
import FraudMeter from '../components/FraudMeter'
import ShapChart from '../components/ShapChart'
import RiskBadge from '../components/RiskBadge'
import StatusBadge from '../components/StatusBadge'

const STATUSES = ['OPEN', 'UNDER_INVESTIGATION', 'CONFIRMED_FRAUD', 'FALSE_POSITIVE', 'CLOSED']

export default function CaseDetail() {
  const { id } = useParams()
  const [kase,    setKase]    = useState(null)
  const [summary, setSummary] = useState(null)
  const [chat,    setChat]    = useState([])
  const [msg,     setMsg]     = useState('')
  const [note,    setNote]    = useState('')
  const [sending, setSending] = useState(false)
  const [status,  setStatus]  = useState('')
  const chatRef = useRef(null)

  useEffect(() => {
    client.get(`/api/v1/cases/${id}`).then(r => { setKase(r.data); setStatus(r.data.status) }).catch(() => {})
    client.get(`/api/v1/investigation/cases/${id}/summary`).then(r => setSummary(r.data)).catch(() => {})
  }, [id])

  useEffect(() => {
    chatRef.current?.scrollTo({ top: chatRef.current.scrollHeight, behavior: 'smooth' })
  }, [chat])

  async function sendMessage(e) {
    e.preventDefault()
    if (!msg.trim()) return
    const userMsg = { role: 'analyst', content: msg }
    setChat(prev => [...prev, userMsg])
    setMsg('')
    setSending(true)
    try {
      const { data } = await client.post('/api/v1/investigation/chat', {
        case_id: id, message: msg, conversation_history: chat,
      })
      setChat(data.conversation_history)
    } catch {
      setChat(prev => [...prev, { role: 'assistant', content: 'Unable to get response. Please try again.' }])
    } finally { setSending(false) }
  }

  async function addNote(e) {
    e.preventDefault()
    if (!note.trim()) return
    try {
      await client.post(`/api/v1/cases/${id}/notes`, { content: note })
      setNote('')
      const r = await client.get(`/api/v1/cases/${id}`)
      setKase(r.data)
    } catch {}
  }

  async function updateStatus(newStatus) {
    try {
      await client.patch(`/api/v1/cases/${id}/status`, { status: newStatus, reason: 'Updated via dashboard' })
      setStatus(newStatus)
      setKase(prev => ({ ...prev, status: newStatus }))
    } catch {}
  }

  if (!kase) return (
    <div className="p-8 flex items-center justify-center h-64">
      <RefreshCw size={22} className="animate-spin text-blue-500" />
    </div>
  )

  return (
    <div className="p-8 max-w-6xl mx-auto">

      {/* Breadcrumb */}
      <Link to="/cases" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-800 mb-5">
        <ChevronLeft size={15} /> Fraud Cases
      </Link>

      {/* Case header */}
      <div className="card p-5 mb-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-mono text-blue-600 bg-blue-50 px-2 py-0.5 rounded">{kase.case_id}</span>
              <RiskBadge level={kase.risk_level} />
              <StatusBadge status={kase.status} />
            </div>
            <h1 className="text-xl font-bold text-slate-900 mt-2">
              ${Number(kase.amount).toLocaleString('en-US')} — {kase.merchant_name}
            </h1>
            <p className="text-sm text-slate-500 mt-1">
              Cardholder: <span className="font-medium text-slate-700">{kase.cardholder_id}</span>
              &nbsp;·&nbsp; MCC: {kase.merchant_category_code}
              &nbsp;·&nbsp; {new Date(kase.created_at).toLocaleString()}
            </p>
          </div>

          {/* Status control */}
          <div className="flex items-center gap-2">
            <Settings2 size={14} className="text-slate-400" />
            <select
              className="input w-52 py-1.5 text-sm"
              value={status}
              onChange={(e) => updateStatus(e.target.value)}
            >
              {STATUSES.map(s => <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>)}
            </select>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">

        {/* LEFT col — ML + AI analysis (3/5) */}
        <div className="lg:col-span-3 space-y-5">

          {/* Fraud score */}
          <div className="card p-6 flex flex-col items-center">
            <FraudMeter score={kase.fraud_probability} />
          </div>

          {/* AI Explanation */}
          <div className="card p-5">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-2">AI Explanation</p>
            <p className="text-sm text-slate-700 leading-relaxed">{kase.fraud_explanation}</p>
          </div>

          {/* SHAP factors */}
          <div className="card p-5">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-4">Risk Factor Analysis (SHAP)</p>
            <ShapChart factors={kase.top_risk_factors ?? []} />
          </div>

          {/* AI Summary */}
          {summary && (
            <div className="card p-5 border-blue-100 bg-blue-50/40">
              <p className="text-xs font-semibold text-blue-600 uppercase tracking-wide mb-2">AI Executive Summary</p>
              <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-line">{summary.executive_summary}</p>
              {summary.key_red_flags?.length > 0 && (
                <div className="mt-3">
                  <p className="text-xs font-semibold text-slate-500 mb-1.5">Key Red Flags</p>
                  <ul className="space-y-1">
                    {summary.key_red_flags.map((f, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-slate-600">
                        <span className="text-red-500 mt-0.5">•</span> {f}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              <div className="mt-3 pt-3 border-t border-blue-100">
                <p className="text-xs font-semibold text-slate-500 mb-0.5">Recommended Action</p>
                <p className="text-sm text-slate-700 font-medium">{summary.recommended_action}</p>
              </div>
            </div>
          )}
        </div>

        {/* RIGHT col — Investigation tools (2/5) */}
        <div className="lg:col-span-2 space-y-5">

          {/* AI Chat */}
          <div className="card flex flex-col h-96">
            <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-100">
              <MessageSquare size={15} className="text-blue-500" />
              <p className="text-sm font-semibold text-slate-700">AI Investigation Chat</p>
            </div>

            <div ref={chatRef} className="flex-1 overflow-y-auto p-4 space-y-3">
              {chat.length === 0 && (
                <p className="text-xs text-slate-300 text-center mt-8">
                  Ask anything about this fraud case.<br />
                  e.g. "Should I block this card?"
                </p>
              )}
              {chat.map((m, i) => (
                <div key={i} className={`flex ${m.role === 'analyst' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[85%] text-xs px-3 py-2 rounded-xl leading-relaxed ${
                    m.role === 'analyst'
                      ? 'bg-blue-600 text-white rounded-br-none'
                      : 'bg-slate-100 text-slate-700 rounded-bl-none'
                  }`}>
                    {m.role === 'analyst' ? m.content : (
                      <ReactMarkdown
                        components={{
                          p: ({ children }) => <p className="mb-1 last:mb-0">{children}</p>,
                          strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                          ol: ({ children }) => <ol className="list-decimal list-inside space-y-0.5 mt-1">{children}</ol>,
                          ul: ({ children }) => <ul className="list-disc list-inside space-y-0.5 mt-1">{children}</ul>,
                          li: ({ children }) => <li>{children}</li>,
                        }}
                      >{m.content}</ReactMarkdown>
                    )}
                  </div>
                </div>
              ))}
              {sending && (
                <div className="flex justify-start">
                  <div className="bg-slate-100 text-slate-400 text-xs px-3 py-2 rounded-xl rounded-bl-none">
                    Thinking…
                  </div>
                </div>
              )}
            </div>

            <form onSubmit={sendMessage} className="flex gap-2 p-3 border-t border-slate-100">
              <input
                className="input text-xs py-1.5 flex-1"
                placeholder="Ask about this case…"
                value={msg}
                onChange={(e) => setMsg(e.target.value)}
              />
              <button type="submit" disabled={sending || !msg.trim()} className="btn-primary px-3 py-1.5">
                <Send size={13} />
              </button>
            </form>
          </div>

          {/* Notes */}
          <div className="card p-4">
            <div className="flex items-center gap-2 mb-3">
              <StickyNote size={14} className="text-slate-400" />
              <p className="text-sm font-semibold text-slate-700">Investigation Notes</p>
            </div>

            <div className="space-y-2 mb-3 max-h-48 overflow-y-auto">
              {(kase.notes ?? []).length === 0 ? (
                <p className="text-xs text-slate-300 text-center py-4">No notes yet</p>
              ) : kase.notes.map((n) => (
                <div key={n.note_id} className="bg-slate-50 rounded-lg p-3 border border-slate-100">
                  <p className="text-xs text-slate-700">{n.content}</p>
                  <p className="text-[10px] text-slate-400 mt-1">{n.analyst} · {new Date(n.created_at).toLocaleString()}</p>
                </div>
              ))}
            </div>

            <form onSubmit={addNote} className="flex gap-2">
              <input
                className="input text-xs py-1.5 flex-1"
                placeholder="Add a note…"
                value={note}
                onChange={(e) => setNote(e.target.value)}
              />
              <button type="submit" className="btn-secondary py-1.5 px-3 text-xs">Add</button>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}
