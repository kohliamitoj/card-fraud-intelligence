import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'
import { ShieldAlert, TrendingUp, CheckCircle, XCircle, ArrowRight } from 'lucide-react'
import client from '../api/client'
import RiskBadge from '../components/RiskBadge'
import StatusBadge from '../components/StatusBadge'

function KpiCard({ label, value, sub, icon: Icon, color }) {
  return (
    <div className="card p-5">
      <div className="flex items-start justify-between mb-3">
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">{label}</p>
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${color}`}>
          <Icon size={16} className="text-white" />
        </div>
      </div>
      <p className="text-2xl font-bold text-slate-900">{value ?? '—'}</p>
      {sub && <p className="text-xs text-slate-400 mt-1">{sub}</p>}
    </div>
  )
}

export default function Dashboard() {
  const [stats, setStats]   = useState(null)
  const [trends, setTrends] = useState([])
  const [cases, setCases]   = useState([])

  useEffect(() => {
    client.get('/api/v1/analytics/dashboard').then(r => setStats(r.data)).catch(() => {})
    client.get('/api/v1/analytics/trends?days=14').then(r => setTrends(r.data.daily_trends ?? [])).catch(() => {})
    client.get('/api/v1/cases/?limit=5').then(r => setCases(r.data)).catch(() => {})
  }, [])

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
        <p className="text-slate-500 text-sm mt-1">Real-time overview of fraud detection performance</p>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <KpiCard label="Total Scored"      value={stats?.total_transactions_scored?.toLocaleString()} sub="transactions" icon={TrendingUp}  color="bg-blue-500" />
        <KpiCard label="Total Cases"       value={stats?.total_cases?.toLocaleString()}               sub={`${stats?.open_cases ?? 0} open`} icon={ShieldAlert} color="bg-orange-500" />
        <KpiCard label="Confirmed Fraud"   value={stats?.confirmed_fraud_cases}                       sub={`${stats?.detection_rate_percent ?? 0}% detection rate`} icon={XCircle}    color="bg-red-500" />
        <KpiCard label="False Positives"   value={stats?.false_positive_cases}                        sub={`${stats?.false_positive_rate_percent ?? 0}% rate`}       icon={CheckCircle} color="bg-green-500" />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">

        {/* Trend chart */}
        <div className="card p-5">
          <p className="text-sm font-semibold text-slate-700 mb-4">Daily Fraud Cases (14 days)</p>
          {trends.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={trends} margin={{ top: 4, right: 8, bottom: 0, left: -20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="_id" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} />
                <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e2e8f0' }} />
                <Line type="monotone" dataKey="total_cases" stroke="#3b82f6" strokeWidth={2} dot={false} name="Total Cases" />
                <Line type="monotone" dataKey="confirmed_fraud" stroke="#ef4444" strokeWidth={2} dot={false} name="Confirmed Fraud" />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-48 flex items-center justify-center text-slate-300 text-sm">No trend data yet</div>
          )}
        </div>

        {/* Fraud amount summary */}
        <div className="card p-5">
          <p className="text-sm font-semibold text-slate-700 mb-4">Fraud Exposure Summary</p>
          <div className="space-y-4 mt-6">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-slate-500">Total Fraud Amount</span>
                <span className="font-bold text-red-600">
                  ${(stats?.total_confirmed_fraud_amount_usd ?? 0).toLocaleString('en-US', { maximumFractionDigits: 0 })}
                </span>
              </div>
              <div className="h-2 bg-slate-100 rounded-full">
                <div className="h-full bg-red-500 rounded-full" style={{ width: '75%' }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-slate-500">Flag Rate</span>
                <span className="font-bold text-amber-600">{stats?.flag_rate_percent ?? 0}%</span>
              </div>
              <div className="h-2 bg-slate-100 rounded-full">
                <div className="h-full bg-amber-400 rounded-full" style={{ width: `${Math.min(stats?.flag_rate_percent ?? 0, 100)}%` }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-slate-500">Critical Cases</span>
                <span className="font-bold text-slate-800">{stats?.critical_cases ?? 0}</span>
              </div>
              <div className="h-2 bg-slate-100 rounded-full">
                <div className="h-full bg-red-700 rounded-full" style={{ width: `${Math.min((stats?.critical_cases ?? 0) * 5, 100)}%` }} />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Recent cases */}
      <div className="card">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
          <p className="text-sm font-semibold text-slate-700">Recent Fraud Cases</p>
          <Link to="/cases" className="text-xs text-blue-600 font-medium hover:underline flex items-center gap-1">
            View all <ArrowRight size={12} />
          </Link>
        </div>
        {cases.length > 0 ? (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100">
                {['Case ID', 'Cardholder', 'Amount', 'Risk', 'Status', 'Date'].map(h => (
                  <th key={h} className="px-5 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {cases.map(c => (
                <tr key={c.case_id} className="table-row" onClick={() => window.location.href = `/cases/${c.case_id}`}>
                  <td className="px-5 py-3 font-mono text-xs text-blue-600">{c.case_id.slice(0, 8)}…</td>
                  <td className="px-5 py-3 text-slate-600">{c.cardholder_id}</td>
                  <td className="px-5 py-3 font-semibold">${Number(c.amount).toLocaleString('en-US')}</td>
                  <td className="px-5 py-3"><RiskBadge level={c.risk_level} /></td>
                  <td className="px-5 py-3"><StatusBadge status={c.status} /></td>
                  <td className="px-5 py-3 text-slate-400">{new Date(c.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="py-12 text-center text-slate-300 text-sm">No cases yet. Score a transaction to create one.</div>
        )}
      </div>
    </div>
  )
}
