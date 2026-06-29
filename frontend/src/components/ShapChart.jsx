const MAX_FACTORS = 8

function formatFeature(name) {
  return name
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())
}

export default function ShapChart({ factors = [] }) {
  if (!factors.length) return null

  const top = factors.slice(0, MAX_FACTORS)
  const maxImpact = Math.max(...top.map((f) => Math.abs(f.impact)), 0.01)

  return (
    <div className="space-y-2.5">
      {top.map((f) => {
        const pct = (Math.abs(f.impact) / maxImpact) * 100
        const isRisk = f.direction === 'increases_risk'
        return (
          <div key={f.feature}>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-600 font-medium">{formatFeature(f.feature)}</span>
              <span className={isRisk ? 'text-red-600 font-semibold' : 'text-green-600 font-semibold'}>
                {isRisk ? '+' : '-'}{Math.abs(f.impact).toFixed(3)}
              </span>
            </div>
            <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-700 ${isRisk ? 'bg-red-500' : 'bg-green-500'}`}
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        )
      })}
    </div>
  )
}
