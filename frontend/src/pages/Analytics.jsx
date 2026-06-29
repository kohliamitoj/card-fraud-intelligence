import { useEffect, useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, LineChart, Line,
} from 'recharts'
import client from '../api/client'

const COLORS = ['#3b82f6', '#ef4444', '#f59e0b', '#10b981', '#8b5cf6', '#06b6d4', '#f97316', '#ec4899']

function Section({ title, children }) {
  return (
    <div className="card p-5">
      <p className="text-sm font-semibold text-slate-700 mb-5">{title}</p>
      {children}
    </div>
  )
}

export default function Analytics() {
  const [mcc,    setMcc]    = useState([])
  const [channel,setChannel]= useState([])
  const [trends, setTrends] = useState([])
  const [stats,  setStats]  = useState(null)

  useEffect(() => {
    client.get('/api/v1/analytics/by-merchant-category').then(r => setMcc(r.data)).catch(() => {})
    client.get('/api/v1/analytics/by-channel').then(r => setChannel(r.data)).catch(() => {})
    client.get('/api/v1/analytics/trends?days=30').then(r => setTrends(r.data.daily_trends ?? [])).catch(() => {})
    client.get('/api/v1/analytics/dashboard').then(r => setStats(r.data)).catch(() => {})
  }, [])

  const channelPie = channel.map(c => ({ name: c._id, value: c.flagged }))

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Analytics</h1>
        <p className="text-slate-500 text-sm mt-1">Fraud patterns, trends, and model performance</p>
      </div>

      {/* Summary KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {[
          { label: 'Transactions Scored', value: stats?.total_transactions_scored?.toLocaleString() ?? '—' },
          { label: 'Detection Rate',      value: `${stats?.detection_rate_percent ?? 0}%` },
          { label: 'False Positive Rate', value: `${stats?.false_positive_rate_percent ?? 0}%` },
          { label: 'Fraud Exposure',      value: `$${(stats?.total_confirmed_fraud_amount_usd ?? 0).toLocaleString('en-US', { maximumFractionDigits: 0 })}` },
        ].map(({ label, value }) => (
          <div key={label} className="card p-4">
            <p className="text-xs text-slate-400 font-medium uppercase tracking-wide">{label}</p>
            <p className="text-xl font-bold text-slate-900 mt-1">{value}</p>
          </div>
        ))}
      </div>

      {/* Charts grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">

        <Section title="30-Day Fraud Trend">
          {trends.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={trends} margin={{ top: 4, right: 8, bottom: 0, left: -20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="_id" tick={{ fontSize: 9, fill: '#94a3b8' }} />
                <YAxis tick={{ fontSize: 9, fill: '#94a3b8' }} />
                <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8, border: '1px solid #e2e8f0' }} />
                <Line type="monotone" dataKey="total_cases"     stroke="#3b82f6" strokeWidth={2} dot={false} name="Total" />
                <Line type="monotone" dataKey="confirmed_fraud" stroke="#ef4444" strokeWidth={2} dot={false} name="Confirmed" />
              </LineChart>
            </ResponsiveContainer>
          ) : <EmptyChart />}
        </Section>

        <Section title="Fraud by Channel">
          {channelPie.filter(c => c.value > 0).length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={channelPie} cx="50%" cy="50%" innerRadius={55} outerRadius={90}
                     dataKey="value" nameKey="name" paddingAngle={3}>
                  {channelPie.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8 }} />
              </PieChart>
            </ResponsiveContainer>
          ) : <EmptyChart />}
        </Section>
      </div>

      <Section title="Top Fraud Merchant Categories (MCC)">
        {mcc.length > 0 ? (
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={mcc.slice(0, 10)} layout="vertical" margin={{ top: 0, right: 20, bottom: 0, left: 60 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 10, fill: '#94a3b8' }} />
              <YAxis dataKey="_id" type="category" tick={{ fontSize: 10, fill: '#64748b' }} width={60} />
              <Tooltip
                contentStyle={{ fontSize: 11, borderRadius: 8, border: '1px solid #e2e8f0' }}
                formatter={(v, name) => [v, name === 'flagged_count' ? 'Flagged' : name]}
              />
              <Bar dataKey="flagged_count" fill="#3b82f6" radius={[0, 4, 4, 0]} name="Flagged" />
            </BarChart>
          </ResponsiveContainer>
        ) : <EmptyChart />}
      </Section>
    </div>
  )
}

function EmptyChart() {
  return <div className="h-48 flex items-center justify-center text-slate-200 text-sm">No data yet</div>
}
