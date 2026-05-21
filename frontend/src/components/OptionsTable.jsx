import { useState, useMemo } from 'react'
import { fmtCurrency, fmtPct, fmtNum, fmtDate, colorClass } from '../utils/format'
import EarningsTrend from './EarningsTrend'
import styles from './DataTable.module.css'

const COLS = [
  { key: 'underlying',       label: 'Underlying',     sortVal: r => r.underlying },
  { key: 'account_label',    label: 'Account',        sortVal: r => r.account_label,    accountOnly: true },
  { key: 'call_put',         label: 'Type',           sortVal: r => r.call_put ?? '' },
  { key: 'strike',           label: 'Strike',         sortVal: r => r.strike ?? -Infinity },
  { key: 'expiration',       label: 'Expiration',     sortVal: r => r.expiration ?? '' },
  { key: 'contracts',        label: 'Contracts',      sortVal: r => r.contracts ?? -Infinity },
  { key: 'avg_cost',         label: 'Avg Cost',       sortVal: r => r.avg_cost ?? -Infinity },
  { key: 'current_price',    label: 'Cur Price',      sortVal: r => r.current_price ?? -Infinity },
  { key: 'current_value',    label: 'Cur Value',      sortVal: r => r.current_value ?? -Infinity },
  { key: 'gl_dollar',        label: '$ G/L',          sortVal: r => r.gl_dollar ?? -Infinity },
  { key: 'gl_pct',           label: '% G/L',          sortVal: r => r.gl_pct ?? -Infinity },
  { key: 'last_purchase_date', label: 'Last Buy',     sortVal: r => r.last_purchase_date ?? '' },
  { key: 'tax_status',       label: 'Tax Status',     sortVal: r => r.tax_status ?? '' },
  { key: 'next_earnings_date', label: 'Next Earnings', sortVal: r => r.next_earnings_date ?? '' },
  { key: 'earnings_history', label: 'Last 3 Earnings', sortable: false },
]

export default function OptionsTable({ rows, byAccount }) {
  const [sortKey, setSortKey] = useState('current_value')
  const [sortDir, setSortDir] = useState('desc')

  function handleSort(col) {
    if (col.sortable === false) return
    if (sortKey === col.key) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortKey(col.key)
      setSortDir('desc')
    }
  }

  const sorted = useMemo(() => {
    if (!rows?.length) return []
    const col = COLS.find(c => c.key === sortKey)
    if (!col || col.sortable === false) return rows
    return [...rows].sort((a, b) => {
      const av = col.sortVal(a)
      const bv = col.sortVal(b)
      if (av < bv) return sortDir === 'asc' ? -1 : 1
      if (av > bv) return sortDir === 'asc' ? 1 : -1
      return 0
    })
  }, [rows, sortKey, sortDir])

  if (!rows?.length) return <div className={styles.empty}>No options positions found.</div>

  const visibleCols = COLS.filter(c => !c.accountOnly || byAccount)

  return (
    <div className={styles.tableWrap}>
      <table className={styles.table}>
        <thead>
          <tr>
            {visibleCols.map(col => (
              <th
                key={col.key}
                className={[
                  col.sortable !== false ? styles.sortable : '',
                  sortKey === col.key ? styles.sortActive : '',
                ].join(' ')}
                onClick={() => handleSort(col)}
              >
                {col.label}
                {col.sortable !== false && sortKey === col.key && (
                  <span className={styles.sortIcon}>{sortDir === 'asc' ? '▲' : '▼'}</span>
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((r, i) => (
            <tr key={i}>
              <td>
                <a
                  href={`https://finance.yahoo.com/quote/${r.underlying}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={styles.tickerLink}
                >
                  {r.underlying}
                </a>
              </td>
              {byAccount && <td className={styles.acct}>{r.account_label}</td>}
              <td>
                {r.call_put && (
                  <span className={`${styles.taxBadge} ${r.call_put === 'CALL' ? styles.long : styles.short}`}>
                    {r.call_put}
                  </span>
                )}
              </td>
              <td className="mono">${fmtNum(r.strike, 0)}</td>
              <td className={styles.date}>{fmtDate(r.expiration)}</td>
              <td className="mono">{fmtNum(r.contracts, 0)}</td>
              <td className="mono">{fmtCurrency(r.avg_cost)}</td>
              <td className="mono">{fmtCurrency(r.current_price)}</td>
              <td className="mono">{fmtCurrency(r.current_value)}</td>
              <td className={`mono ${colorClass(r.gl_dollar)}`}>{fmtCurrency(r.gl_dollar)}</td>
              <td className={`mono ${colorClass(r.gl_pct)}`}>{fmtPct(r.gl_pct)}</td>
              <td className={styles.date}>{fmtDate(r.last_purchase_date)}</td>
              <td>
                {r.tax_status
                  ? <span className={`${styles.taxBadge} ${r.tax_status === 'Long Term' ? styles.long : styles.short}`}>
                      {r.tax_status}
                    </span>
                  : <span className="neutral">—</span>
                }
              </td>
              <td className={styles.date}>{fmtDate(r.next_earnings_date)}</td>
              <td><EarningsTrend history={r.earnings_history} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
