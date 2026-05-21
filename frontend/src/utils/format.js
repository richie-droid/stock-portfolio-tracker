export function fmtCurrency(val, decimals = 2) {
  if (val == null || isNaN(val)) return '—'
  const abs = Math.abs(val)
  const formatted = abs.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
  return val < 0 ? `-$${formatted}` : `$${formatted}`
}

export function fmtPct(val, decimals = 2) {
  if (val == null || isNaN(val)) return '—'
  const sign = val >= 0 ? '+' : ''
  return `${sign}${Number(val).toFixed(decimals)}%`
}

export function fmtNum(val, decimals = 3) {
  if (val == null || isNaN(val)) return '—'
  return Number(val).toLocaleString('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: decimals,
  })
}

export function fmtDate(val) {
  if (!val) return '—'
  return val.slice(0, 10)
}

export function colorClass(val) {
  if (val == null || isNaN(val)) return 'neutral'
  return val >= 0 ? 'positive' : 'negative'
}
