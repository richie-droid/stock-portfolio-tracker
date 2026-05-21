import styles from './EarningsTrend.module.css'

function fmtQuarter(dateStr) {
  if (!dateStr) return ''
  // Yahoo returns '4Q2024' or '2024-10-01' style
  const isoMatch = dateStr.match(/^(\d{4})-(\d{2})/)
  if (isoMatch) {
    const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    return `${months[parseInt(isoMatch[2], 10) - 1]} '${isoMatch[1].slice(2)}`
  }
  // '4Q2024' → Q4 '24
  const qMatch = dateStr.match(/^(\d)Q(\d{4})/)
  if (qMatch) return `Q${qMatch[1]} '${qMatch[2].slice(2)}`
  return dateStr.slice(0, 7)
}

export default function EarningsTrend({ history }) {
  if (!history?.length) return <span className="neutral">—</span>

  const last3 = [...history].slice(-3)

  return (
    <div className={styles.chips}>
      {last3.map((q, i) => {
        const pct = q.surprise_pct
        const label = pct != null
          ? `${pct >= 0 ? '+' : ''}${pct.toFixed(1)}%`
          : (q.beat ? 'Beat' : 'Miss')
        const tooltip = `${fmtQuarter(q.date)}: Est $${q.estimated_eps} / Act $${q.actual_eps} (${label})`

        return (
          <span
            key={i}
            className={`${styles.chip} ${q.beat ? styles.beat : styles.miss}`}
            title={tooltip}
          >
            <span className={styles.qLabel}>{fmtQuarter(q.date)}</span>
            <span className={styles.pct}>{label}</span>
          </span>
        )
      })}
    </div>
  )
}
