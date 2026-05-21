import { fmtCurrency, fmtPct, fmtNum, fmtDate, colorClass } from '../utils/format'
import EarningsTrend from './EarningsTrend'
import styles from './DataTable.module.css'

export default function StocksTable({ rows, byAccount }) {
  if (!rows?.length) return <div className={styles.empty}>No stock positions found.</div>

  return (
    <div className={styles.tableWrap}>
      <table className={styles.table}>
        <thead>
          <tr>
            <th>Ticker</th>
            {byAccount && <th>Account</th>}
            <th className="mono">Qty</th>
            <th className="mono">Avg Cost</th>
            <th className="mono">Cur Price</th>
            <th className="mono">Cur Value</th>
            <th className="mono">$ G/L</th>
            <th className="mono">% G/L</th>
            <th>Last Buy</th>
            <th>Tax Status</th>
            <th>Next Earnings</th>
            <th>6M Earnings</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>
              <td><span className={styles.ticker}>{r.symbol}</span></td>
              {byAccount && <td className={styles.acct}>{r.account_label}</td>}
              <td className="mono">{fmtNum(r.quantity, 3)}</td>
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
