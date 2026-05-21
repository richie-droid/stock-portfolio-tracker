import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export async function fetchDashboard(positionsFile) {
  const form = new FormData()
  form.append('positions_file', positionsFile)
  const res = await api.post('/dashboard', form)
  return res.data
}

export async function uploadHistory(files) {
  const form = new FormData()
  files.forEach(f => form.append('files', f))
  const res = await api.post('/upload/history', form)
  return res.data
}

export async function getHistoryStats() {
  const res = await api.get('/history/stats')
  return res.data
}

export function exportHistoryUrl() {
  return '/api/history/export'
}
