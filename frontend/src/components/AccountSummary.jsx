import { fmtCurrency } from '../utils/format'
import styles from './AccountSummary.module.css'

export default function AccountSummary({ summaries }) {
  if (!summaries?.length) return null

  const fields = [
    { key: 'current_value',       label: 'Current Value',     sign: false },
    { key: 'unrealized_gl',       label: 'Unrealized G/L',    sign: true  },
    { key: 'fresh_funds_invested',label: 'Fresh Funds In',    sign: false },
    { key: 'cash_taken_out',      label: 'Cash Taken Out',    sign: false },
    { key: 'realized_gains',      label: 'Realized Gains',    sign: true  },
    { key: 'dividends_received',  label: 'Dividends',         sign: false },
  ]

  return (
    <div className={styles.wrapper}>
      <div className={styles.grid}>
        {summaries.map(acct => (
          <div key={acct.account_number} className={`${styles.card} ${acct.account_number === 'TOTAL' ? styles.total : ''}`}>
            <div className={styles.acctName}>{acct.account_label}</div>
            {fields.map(f => (
              <div key={f.key} className={styles.metric}>
                <span className={styles.label}>{f.label}</span>
                <span className={`${styles.value} mono ${f.sign ? (acct[f.key] >= 0 ? 'positive' : 'negative') : ''}`}>
                  {fmtCurrency(acct[f.key])}
                </span>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}
