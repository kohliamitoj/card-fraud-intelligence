import clsx from 'clsx'

const styles = {
  LOW:      'bg-green-50 text-green-700 ring-1 ring-green-200',
  MEDIUM:   'bg-amber-50 text-amber-700 ring-1 ring-amber-200',
  HIGH:     'bg-orange-50 text-orange-700 ring-1 ring-orange-200',
  CRITICAL: 'bg-red-50 text-red-700 ring-1 ring-red-200',
}

const dots = {
  LOW:      'bg-green-500',
  MEDIUM:   'bg-amber-500',
  HIGH:     'bg-orange-500',
  CRITICAL: 'bg-red-500',
}

export default function RiskBadge({ level }) {
  return (
    <span className={clsx('inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold', styles[level] ?? styles.LOW)}>
      <span className={clsx('w-1.5 h-1.5 rounded-full', dots[level] ?? dots.LOW)} />
      {level}
    </span>
  )
}
