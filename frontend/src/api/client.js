import axios from 'axios'

// Relative URLs: the Vite dev server proxies /api to the FastAPI backend.
export const api = axios.create({ baseURL: '', timeout: 30000 })

export function errorMessage(error) {
  const detail = error?.response?.data?.detail
  if (detail) return typeof detail === 'string' ? detail : JSON.stringify(detail)
  if (!error?.response) return 'Cannot reach the backend. Is it running on http://127.0.0.1:8000?'
  return error.message
}