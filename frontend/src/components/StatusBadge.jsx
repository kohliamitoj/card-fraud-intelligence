import clsx from 'clsx'

const styles = {
  OPEN:                 'bg-blue-50 text-blue-700 ring-1 ring-blue-200',
  UNDER_INVESTIGATION:  'bg-purple-50 text-purple-700 ring-1 ring-purple-200',
  CONFIRMED_FRAUD:      'bg-red-50 text-red-700 ring-1 ring-red-200',
  FALSE_POSITIVE:       'bg-green-50 text-green-700 ring-1 ring-green-200',
  CLOSED:               'bg-slate-100 text-slate-600 ring-1 ring-slate-200',
}

const labels = {
  OPEN:                'Open',
  UNDER_INVESTIGATION: 'Investigating',
  CONFIRMED_FRAUD:     'Confirmed Fraud',
  FALSE_POSITIVE:      'False Positive',
  CLOSED:              'Closed',
}

export default function StatusBadge({ status }) {
  return (
    <span className={clsx('inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold', styles[status] ?? styles.OPEN)}>
      {labels[status] ?? status}
    </span>
  )
}
