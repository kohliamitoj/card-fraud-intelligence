import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Filter, ChevronLeft, ChevronRight } from 'lucide-react'
import client from '../api/client'
import RiskBadge from '../components/RiskBadge'
import StatusBadge from '../components/StatusBadge'

const STATUSES   = ['', 'OPEN', 'UNDER_INVESTIGATION', 'CONFIRMED_FRAUD', 'FALSE_POSITIVE', 'CLOSED']
const RISK_LEVELS = ['', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
const PAGE_SIZE  = 20

export default function Cases() {
  const navigate = useNavigate()
  const [cases,     setCases]     = useState([])
  const [status,    setStatus]    = useState('')
  const [risk,      setRisk]      = useState('')
  const [page,      setPage]      = useState(0)
  const [loading,   setLoading]   = useState(false)
  const [hasMore,   setHasMore]   = useState(false)

  async function load(s = status, r = risk, p = page) {
    setLoading(true)
    try {
      const params = new URLSearchParams({ limit: PAGE_SIZE, skip: p * PAGE_SIZE })
      if (s) params.set('status', s)
      if (r) params.set('risk_level', r)
      const { data } = await client.get(`/api/v1/cases/?${params}`)
      setCases(data)
      setHasMore(data.length === PAGE_SIZE)
    } catch {}
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  function applyFilter(s, r) {
    setStatus(s); setRisk(r); setPage(0); load(s, r, 0)
  }

  function changePage(delta) {
    const next = page + delta
    setPage(next); load(status, risk, next)
  }

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">Fraud Cases</h1>
        <p className="text-slate-500 text-sm mt-1">All flagged transactions requiring investigation</p>
      </div>

      {/* Filters */}
      <div className="card p-4 mb-5 flex flex-wrap items-center gap-3">
        <Filter size={15} className="text-slate-400" />
        <select className="input w-44 py-1.5" value={status} onChange={(e) => applyFilter(e.target.value, risk)}>
          <option value="">All Statuses</option>
          {STATUSES.filter(Boolean).map(s => <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>)}
        </select>
        <select className="input w-36 py-1.5" value={risk} onChange={(e) => applyFilter(status, e.target.value)}>
          <option value="">All Risk Levels</option>
          {RISK_LEVELS.filter(Boolean).map(r => <option key={r} value={r}>{r}</option>)}
        </select>
        <button onClick={() => applyFilter('', '')} className="btn-secondary py-1.5 text-xs">Clear</button>
        <span className="ml-auto text-xs text-slate-400">{cases.length} results</span>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              {['Case ID', 'Cardholder', 'Amount', 'Merchant', 'Risk', 'Status', 'Date'].map(h => (
                <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              [...Array(6)].map((_, i) => (
                <tr key={i} className="border-b border-slate-100">
                  {[...Array(7)].map((_, j) => (
                    <td key={j} className="px-4 py-3"><div className="h-4 bg-slate-100 rounded animate-pulse" /></td>
                  ))}
                </tr>
              ))
            ) : cases.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-16 text-center text-slate-300 text-sm">No cases found</td>
              </tr>
            ) : cases.map(c => (
              <tr key={c.case_id} className="table-row border-b border-slate-100" onClick={() => navigate(`/cases/${c.case_id}`)}>
                <td className="px-4 py-3 font-mono text-xs text-blue-600">{c.case_id.slice(0, 8)}…</td>
                <td className="px-4 py-3 text-slate-600 font-medium">{c.cardholder_id}</td>
                <td className="px-4 py-3 font-semibold text-slate-800">${Number(c.amount).toLocaleString('en-US')}</td>
                <td className="px-4 py-3 text-slate-500 max-w-[140px] truncate">{c.merchant_name ?? '—'}</td>
                <td className="px-4 py-3"><RiskBadge level={c.risk_level} /></td>
                <td className="px-4 py-3"><StatusBadge status={c.status} /></td>
                <td className="px-4 py-3 text-slate-400 text-xs">{new Date(c.created_at).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* Pagination */}
        <div className="flex items-center justify-between px-4 py-3 border-t border-slate-100 bg-slate-50">
          <button onClick={() => changePage(-1)} disabled={page === 0} className="btn-secondary py-1.5 text-xs flex items-center gap-1 disabled:opacity-40">
            <ChevronLeft size={14} /> Previous
          </button>
          <span className="text-xs text-slate-500">Page {page + 1}</span>
          <button onClick={() => changePage(1)} disabled={!hasMore} className="btn-secondary py-1.5 text-xs flex items-center gap-1 disabled:opacity-40">
            Next <ChevronRight size={14} />
          </button>
        </div>
      </div>
    </div>
  )
}
