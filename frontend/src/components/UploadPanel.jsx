import { useState, useRef } from 'react'
import { Upload, RefreshCw, Download, Database } from 'lucide-react'
import { uploadHistory, exportHistoryUrl } from '../utils/api'
import styles from './UploadPanel.module.css'

export default function UploadPanel({ onLoad, historyStats, loading, hasData, positionsDate }) {
  const [posFile, setPosFile] = useState(null)
  const [histFiles, setHistFiles] = useState([])
  const [histUploading, setHistUploading] = useState(false)
  const [histMsg, setHistMsg] = useState(null)
  const posRef = useRef()
  const histRef = useRef()

  async function handleHistUpload() {
    if (!histFiles.length) return
    setHistUploading(true)
    setHistMsg(null)
    try {
      const res = await uploadHistory(histFiles)
      setHistMsg(res.message)
      setHistFiles([])
    } catch (e) {
      setHistMsg('Error uploading history: ' + (e.response?.data?.detail || e.message))
    } finally {
      setHistUploading(false)
    }
  }

  function handleLoad() {
    if (!posFile) return
    onLoad(posFile)
    setPosFile(null)
    if (posRef.current) posRef.current.value = ''
  }

  return (
    <div className={styles.panel}>
      <div className={styles.section}>
        <div className={styles.sectionLabel}>
          <RefreshCw size={13} /> Positions
          {hasData && positionsDate && (
            <span className={styles.statsBadge}>last uploaded {positionsDate}</span>
          )}
        </div>
        <div className={styles.row}>
          <input
            ref={posRef}
            type="file"
            accept=".csv"
            className={styles.hidden}
            onChange={e => setPosFile(e.target.files[0])}
          />
          <button className={styles.fileBtn} onClick={() => posRef.current.click()}>
            <Upload size={13} />
            {posFile ? posFile.name : (hasData ? 'Select New Positions CSV' : 'Select Positions CSV')}
          </button>
          <button
            className={styles.loadBtn}
            disabled={!posFile || loading}
            onClick={handleLoad}
          >
            {loading ? 'Loading...' : (hasData ? 'Refresh Dashboard' : 'Load Dashboard')}
          </button>
        </div>
      </div>

      <div className={styles.divider} />

      <div className={styles.section}>
        <div className={styles.sectionLabel}>
          <Database size={13} /> History
          {historyStats?.rows > 0 && (
            <span className={styles.statsBadge}>
              {historyStats.rows.toLocaleString()} rows · {historyStats.earliest_date} → {historyStats.latest_date}
            </span>
          )}
        </div>
        <div className={styles.row}>
          <input
            ref={histRef}
            type="file"
            accept=".csv"
            multiple
            className={styles.hidden}
            onChange={e => setHistFiles(Array.from(e.target.files))}
          />
          <button className={styles.fileBtn} onClick={() => histRef.current.click()}>
            <Upload size={13} />
            {histFiles.length ? `${histFiles.length} file(s) selected` : 'Select History CSV(s)'}
          </button>
          <button
            className={styles.loadBtn}
            disabled={!histFiles.length || histUploading}
            onClick={handleHistUpload}
          >
            {histUploading ? 'Uploading...' : 'Upload & Merge'}
          </button>
          {historyStats?.rows > 0 && (
            <a href={exportHistoryUrl()} className={styles.exportBtn} download>
              <Download size={13} /> Export
            </a>
          )}
        </div>
        {histMsg && <div className={styles.histMsg}>{histMsg}</div>}
      </div>
    </div>
  )
}
