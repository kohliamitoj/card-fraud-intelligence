import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Zap, RefreshCw, ArrowRight, CheckCircle, AlertTriangle } from 'lucide-react'
import client from '../api/client'
import FraudMeter from '../components/FraudMeter'
import ShapChart from '../components/ShapChart'
import RiskBadge from '../components/RiskBadge'

const SUSPICIOUS = {
  transaction_id: `TXN-${Date.now()}`,
  cardholder_id: 'CH-0042',
  card_last4: '7823',
  card_type: 'VISA',
  amount: 95000,
  currency: 'USD',
  merchant_id: 'M-9912',
  merchant_name: 'CryptoXchange Global',
  merchant_category_code: '6051',
  channel: 'ONLINE',
  location_city: 'Lagos',
  location_country: 'NG',
  timestamp: new Date().toISOString(),
}

const LEGIT = {
  transaction_id: `TXN-${Date.now() + 1}`,
  cardholder_id: 'CH-0108',
  card_last4: '4421',
  card_type: 'MASTERCARD',
  amount: 142,
  currency: 'USD',
  merchant_id: 'M-0022',
  merchant_name: 'Whole Foods Market',
  merchant_category_code: '5411',
  channel: 'POS',
  location_city: 'Austin',
  location_country: 'US',
  timestamp: new Date().toISOString(),
}

const FIELDS = [
  { key: 'amount',                label: 'Amount (USD)',  type: 'number' },
  { key: 'cardholder_id',         label: 'Cardholder ID', type: 'text' },
  { key: 'merchant_name',         label: 'Merchant Name', type: 'text' },
  { key: 'merchant_category_code',label: 'MCC Code',      type: 'text' },
  { key: 'channel',               label: 'Channel',       type: 'select', options: ['POS', 'ONLINE', 'ATM', 'CONTACTLESS'] },
  { key: 'card_type',             label: 'Card Type',     type: 'select', options: ['VISA', 'MASTERCARD', 'AMEX', 'RUPAY'] },
  { key: 'location_city',         label: 'City',          type: 'text' },
  { key: 'location_country',      label: 'Country Code',  type: 'text' },
]

export default function Demo() {
  const [form, setForm]       = useState(SUSPICIOUS)
  const [result, setResult]   = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')

  function loadSuspicious() {
    setForm({ ...SUSPICIOUS, transaction_id: `TXN-${Date.now()}` })
    setResult(null)
    setError('')
  }

  function loadLegit() {
    setForm({ ...LEGIT, transaction_id: `TXN-${Date.now()}` })
    setResult(null)
    setError('')
  }

  async function score(e) {
    e.preventDefault()
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const payload = { ...form, amount: parseFloat(form.amount) }
      const { data } = await client.post('/api/v1/transactions/score', payload)
      setResult(data)
    } catch (err) {
      setError(err.response?.data?.detail ?? 'Failed to score transaction. Is the API running?')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-8 max-w-6xl mx-auto">

      {/* Page header */}
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-1">
          <Zap size={20} className="text-blue-600" />
          <h1 className="text-2xl font-bold text-slate-900">Live Fraud Detection Demo</h1>
          <span className="ml-2 text-xs bg-green-100 text-green-700 font-semibold px-2 py-0.5 rounded-full">● LIVE</span>
        </div>
      </div>

      {/* Preset buttons */}
      <div className="flex gap-3 mb-6">
        <button onClick={loadSuspicious} className="flex items-center gap-2 px-4 py-2 bg-red-50 hover:bg-red-100 text-red-700 text-sm font-semibold rounded-lg border border-red-200 transition-colors">
          <AlertTriangle size={14} /> Load Suspicious Example
        </button>
        <button onClick={loadLegit} className="flex items-center gap-2 px-4 py-2 bg-green-50 hover:bg-green-100 text-green-700 text-sm font-semibold rounded-lg border border-green-200 transition-colors">
          <CheckCircle size={14} /> Load Legitimate Example
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* LEFT — Transaction form */}
        <div className="card p-6">
          <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wide mb-5">Transaction Details</h2>
          <form onSubmit={score} className="space-y-4">
            {FIELDS.map(({ key, label, type, options }) => (
              <div key={key}>
                <label className="label">{label}</label>
                {type === 'select' ? (
                  <select
                    className="input"
                    value={form[key] ?? ''}
                    onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                  >
                    {options.map((o) => <option key={o}>{o}</option>)}
                  </select>
                ) : (
                  <input
                    type={type}
                    className="input"
                    value={form[key] ?? ''}
                    onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                    required
                  />
                )}
              </div>
            ))}

            {error && (
              <p className="text-red-600 text-sm bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</p>
            )}

            <button type="submit" disabled={loading} className="btn-primary w-full py-2.5 flex items-center justify-center gap-2 mt-2">
              {loading
                ? <><RefreshCw size={15} className="animate-spin" /> Scoring…</>
                : <><Zap size={15} /> Score Transaction</>
              }
            </button>
          </form>
        </div>

        {/* RIGHT — Results */}
        <div className="space-y-4">
          {!result && !loading && (
            <div className="card p-10 flex flex-col items-center justify-center text-center h-full min-h-64">
              <div className="w-14 h-14 bg-slate-100 rounded-full flex items-center justify-center mb-4">
                <Zap size={24} className="text-slate-300" />
              </div>
              <p className="text-slate-400 text-sm font-medium">Results will appear here</p>
              <p className="text-slate-300 text-xs mt-1">Submit a transaction to see fraud analysis</p>
            </div>
          )}

          {loading && (
            <div className="card p-10 flex flex-col items-center justify-center min-h-64">
              <RefreshCw size={28} className="text-blue-500 animate-spin mb-3" />
              <p className="text-slate-500 text-sm font-medium">Analysing transaction…</p>
            </div>
          )}

          {result && (
            <div className="space-y-4 fade-in">

              {/* Fraud meter */}
              <div className="card p-6 flex flex-col items-center">
                <FraudMeter score={result.fraud_probability} />
                <div className="flex items-center gap-3 mt-4">
                  <RiskBadge level={result.risk_level} />
                  {result.is_flagged
                    ? <span className="text-xs font-semibold text-red-600 bg-red-50 border border-red-200 px-2.5 py-0.5 rounded-full">FLAGGED</span>
                    : <span className="text-xs font-semibold text-green-600 bg-green-50 border border-green-200 px-2.5 py-0.5 rounded-full">CLEAR</span>
                  }
                </div>
              </div>

              {/* Explanation */}
              <div className="card p-5">
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Explanation</p>
                <p className="text-sm text-slate-700 leading-relaxed">{result.fraud_explanation}</p>
              </div>

              {/* SHAP Risk Factors */}
              {result.top_risk_factors?.length > 0 && (
                <div className="card p-5">
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-4">Top Risk Factors</p>
                  <ShapChart factors={result.top_risk_factors} />
                </div>
              )}

              {/* Case link */}
              {result.case_id && (
                <Link
                  to={`/cases/${result.case_id}`}
                  className="flex items-center justify-between card p-4 hover:border-blue-300 hover:bg-blue-50 transition-colors group"
                >
                  <div>
                    <p className="text-sm font-semibold text-slate-700 group-hover:text-blue-700">View Investigation Case</p>
                    <p className="text-xs text-slate-400 mt-0.5">Case ID: {result.case_id}</p>
                  </div>
                  <ArrowRight size={16} className="text-slate-400 group-hover:text-blue-600" />
                </Link>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
