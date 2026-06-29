import { useEffect, useState } from 'react'

const R = 80
const C = Math.PI * R  // semicircle circumference ≈ 251.33

function arcColor(score) {
  if (score >= 0.85) return '#dc2626'  // red-600
  if (score >= 0.65) return '#ea580c'  // orange-600
  if (score >= 0.40) return '#d97706'  // amber-600
  return '#16a34a'                      // green-600
}

function riskLabel(score) {
  if (score >= 0.85) return 'CRITICAL'
  if (score >= 0.65) return 'HIGH'
  if (score >= 0.40) return 'MEDIUM'
  return 'LOW'
}

export default function FraudMeter({ score = 0 }) {
  const [displayed, setDisplayed] = useState(0)

  useEffect(() => {
    const start = performance.now()
    const from  = displayed
    const to    = score
    const dur   = 1300

    function tick(now) {
      const t = Math.min((now - start) / dur, 1)
      const eased = 1 - Math.pow(1 - t, 3)
      setDisplayed(from + (to - from) * eased)
      if (t < 1) requestAnimationFrame(tick)
    }
    requestAnimationFrame(tick)
  }, [score])

  const color = arcColor(score)
  const dash  = `${displayed * C} ${C}`

  return (
    <div className="flex flex-col items-center select-none">
      <svg width="220" height="130" viewBox="0 0 220 130">
        {/* Track */}
        <path
          d="M 30 110 A 80 80 0 0 0 190 110"
          fill="none"
          stroke="#e2e8f0"
          strokeWidth="14"
          strokeLinecap="round"
        />
        {/* Progress arc */}
        <path
          d="M 30 110 A 80 80 0 0 0 190 110"
          fill="none"
          stroke={color}
          strokeWidth="14"
          strokeLinecap="round"
          strokeDasharray={dash}
          className="gauge-arc"
        />
        {/* Center score */}
        <text x="110" y="96" textAnchor="middle" fontSize="32" fontWeight="800" fill={color} fontFamily="Inter, sans-serif">
          {Math.round(displayed * 100)}%
        </text>
        <text x="110" y="116" textAnchor="middle" fontSize="11" fill="#94a3b8" fontFamily="Inter, sans-serif" letterSpacing="1">
          FRAUD SCORE
        </text>
      </svg>

      <div className="mt-1 flex items-center justify-between w-48 text-xs text-slate-400 px-1">
        <span>0%</span>
        <span className="font-semibold text-sm" style={{ color }}>{riskLabel(score)}</span>
        <span>100%</span>
      </div>
    </div>
  )
}
