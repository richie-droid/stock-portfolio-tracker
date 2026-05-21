import { useState, useEffect } from 'react'
import { fetchDashboard, getDashboard, getHistoryStats } from './utils/api'
import UploadPanel from './components/UploadPanel'
import AccountSummary from './components/AccountSummary'
import StocksTable from './components/StocksTable'
import OptionsTable from './components/OptionsTable'
import styles from './App.module.css'

export default function App() {
  const [dashboard, setDashboard] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [historyStats, setHistoryStats] = useState(null)
  const [viewMode, setViewMode] = useState('consolidated')

  useEffect(() => {
    async function autoLoad() {
      try {
        const [data, stats] = await Promise.all([getDashboard(), getHistoryStats()])
        if (data) setDashboard(data)
        if (stats) setHistoryStats(stats)
      } catch {
        // non-fatal — user can still upload
      } finally {
        setLoading(false)
      }
    }
    autoLoad()
  }, [])

  async function handleLoad(posFile) {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchDashboard(posFile)
      setDashboard(data)
      if (data.history_stats) setHistoryStats(data.history_stats)
    } catch (e) {
      setError(e.response?.data?.detail || e.message || 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  const byAccount = viewMode === 'by_account'
  const stocks = byAccount ? dashboard?.stocks_by_account : dashboard?.stocks_consolidated
  const options = byAccount ? dashboard?.options_by_account : dashboard?.options_consolidated

  return (
    <div className={styles.app}>
      <header className={styles.header}>
        <div className={styles.headerInner}>
          <div className={styles.brand}>
            <span className={styles.brandMark}>▸</span>
            <span className={styles.brandName}>Portfolio</span>
            <span className={styles.brandSub}>Tracker</span>
          </div>
          {dashboard && (
            <div className={styles.toggle}>
              <span className={styles.toggleLabel}>View</span>
              <button
                className={`${styles.toggleBtn} ${viewMode === 'consolidated' ? styles.active : ''}`}
                onClick={() => setViewMode('consolidated')}
              >
                Consolidated
              </button>
              <button
                className={`${styles.toggleBtn} ${viewMode === 'by_account' ? styles.active : ''}`}
                onClick={() => setViewMode('by_account')}
              >
                By Account
              </button>
            </div>
          )}
        </div>
      </header>

      <main className={styles.main}>
        <UploadPanel
          onLoad={handleLoad}
          historyStats={historyStats}
          loading={loading}
          hasData={!!dashboard}
          positionsDate={dashboard?.positions_date}
        />

        {error && (
          <div className={styles.error}>
            <strong>Error:</strong> {error}
          </div>
        )}

        {loading && (
          <div className={styles.loading}>
            <span className={styles.spinner} />
            {dashboard ? 'Refreshing positions & fetching market data...' : 'Loading portfolio...'}
          </div>
        )}

        {dashboard && !loading && (
          <>
            <AccountSummary summaries={dashboard.account_summaries} />

            <section className={styles.section}>
              <div className={styles.sectionHeader}>
                <h2 className={styles.sectionTitle}>Stocks</h2>
                <span className={styles.rowCount}>{stocks?.length || 0} positions</span>
              </div>
              <StocksTable rows={stocks} byAccount={byAccount} />
            </section>

            <section className={styles.section}>
              <div className={styles.sectionHeader}>
                <h2 className={styles.sectionTitle}>Options</h2>
                <span className={styles.rowCount}>{options?.length || 0} positions</span>
              </div>
              <OptionsTable rows={options} byAccount={byAccount} />
            </section>
          </>
        )}

        {!dashboard && !loading && !error && (
          <div className={styles.empty}>
            <div className={styles.emptyIcon}>◈</div>
            <div className={styles.emptyText}>Upload a positions file to get started</div>
            <div className={styles.emptyHint}>
              Export from Fidelity → Accounts → Portfolio Positions → Download
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
