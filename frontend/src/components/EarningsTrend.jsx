import styles from './EarningsTrend.module.css'

export default function EarningsTrend({ history }) {
  if (!history?.length) return <span className="neutral">—</span>

  // Show up to 6 quarters, oldest first (left to right)
  const quarters = [...history].reverse().slice(-6)

  return (
    <div className={styles.trend}>
      {quarters.map((q, i) => {
        const pct = q.surprise_pct
        const label = pct != null
          ? `${q.beat ? '+' : ''}${pct.toFixed(1)}%`
          : (q.beat ? 'Beat' : 'Miss')

        return (
          <div
            key={i}
            className={`${styles.dot} ${q.beat ? styles.beat : styles.miss}`}
            title={`${q.date}: EPS Est ${q.estimated_eps} / Act ${q.actual_eps} (${label})`}
          >
            <span className={styles.label}>{label}</span>
          </div>
        )
      })}
    </div>
  )
}
